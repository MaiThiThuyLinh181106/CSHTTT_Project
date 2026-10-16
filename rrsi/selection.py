# Copyright 2026 The rrsi Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Algorithm 2 of the paper, the selection side, as pure functions.

For every screened candidate H' with measurement (S', C'):

    Delta S = S' - S_t,   Delta C = (C' - C_t) / C_t
    c = [Delta C <= beta0 + beta1 Delta S]             if Delta S > delta      Eq. (tokenbudget)
        [w_s Delta S - w_c Delta C + w_n nu(l') > 0]   otherwise
    admissible  iff  S' >= S* - delta  and  c  (and every domain guard holds)  Eq. (floor)

    H_{t+1} = argmax_{H' admissible} S',  or H_t if none is admissible
    S*      = max(S*, S_{t+1})
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .components import novelty
from .evaluate import EvalResult, relative_cost_change


def diversity_penalty(edit_components: list[str], incumbent_counts: dict) -> float:
    """Concentration-based diversity penalty (Exp 4 regularization).

    Returns a value in [0, 1] measuring how much the candidate's edit
    components overlap with the already-saturated components in the history.
    Concretely:

        concentration = max_c( count(c in history) / total_accepted_edits )

    If the candidate's dominant component equals the history's dominant
    component, the penalty equals `concentration`; otherwise 0.  This
    discourages the proposer from repeatedly re-proposing the same component
    type once it already dominates, without blocking it outright.

    The penalty is applied only inside the noise band (shaped rule), so it
    never blocks an edit that produced a clear score gain.
    """
    if not incumbent_counts or not edit_components:
        return 0.0
    total = sum(incumbent_counts.values())
    if total == 0:
        return 0.0
    # Component with the highest accepted-edit share in the history.
    dominant = max(incumbent_counts, key=incumbent_counts.get)
    concentration = incumbent_counts[dominant] / total
    # Candidate's own dominant component.
    cand_counts: dict[str, int] = {}
    for c in edit_components:
        cand_counts[c] = cand_counts.get(c, 0) + 1
    cand_dominant = max(cand_counts, key=cand_counts.get)
    # Penalise only when the candidate re-uses the already-saturated component.
    return concentration if cand_dominant == dominant else 0.0

@dataclass
class Candidate:
    variant: str
    edits: list[dict]                     # each tagged (component, hypothesis, ...)
    ev: EvalResult | None = None
    diff_path: str | None = None
    branch: str | None = None
    commit: str | None = None
    gate_failure: str | None = None       # critic_reject / smoke_fail / eval_invalid
    detail: str = ""

    @property
    def components(self) -> list[str]:
        return [e.get("component") for e in self.edits if e.get("component")]


@dataclass
class Decision:
    variant: str
    admissible: bool
    reason: str
    S: float | None = None
    C: float | None = None
    delta_S: float | None = None
    delta_C: float | None = None
    novelty: int = 0
    guards: list = field(default_factory=list)

    def to_json(self) -> dict:
        return self.__dict__


def cost_rule(delta_S: float, delta_C: float, nov: int, delta: float,
              cfg, div_pen: float = 0.0) -> tuple[bool, str]:
    """c of Algorithm 2, line 5.

    Optionally applies an edit-history diversity penalty (Exp 4):
        shaped += -w_div * div_pen
    where div_pen is the concentration score returned by diversity_penalty().
    The penalty is applied only in the noise-band (shaped) branch; the
    token-budget branch for clear gains is unaffected.
    """
    if delta_S > delta:
        budget = cfg.beta0 + cfg.beta1 * delta_S
        ok = delta_C <= budget
        return ok, (f"gain {delta_S:+.4f} > delta {delta:.4f}; cost change "
                    f"{delta_C:+.3f} {'<=' if ok else '>'} budget {budget:.3f} "
                    f"(beta0 {cfg.beta0} + beta1 {cfg.beta1} * dS)")
    w_div = getattr(cfg, "w_div", 0.0)
    shaped = cfg.w_s * delta_S - cfg.w_c * delta_C + cfg.w_n * nov - w_div * div_pen
    ok = shaped > 0
    div_str = f" - {w_div}*div({div_pen:.2f})" if w_div else ""
    return ok, (f"gain {delta_S:+.4f} within delta {delta:.4f}; shaped "
                f"{cfg.w_s}*dS - {cfg.w_c}*dC + {cfg.w_n}*nu{div_str} = {shaped:+.4f} "
                f"{'>' if ok else '<='} 0 (nu={nov}, div_pen={div_pen:.2f})")


def judge(cand: Candidate, incumbent: EvalResult, S_star: float, delta: float,
          cfg, incumbent_counts: dict, guards: list[str] | None = None) -> Decision:
    ev = cand.ev
    if ev is None:
        return Decision(cand.variant, False, cand.gate_failure or "not evaluated")
    dS = ev.S - incumbent.S
    dC = relative_cost_change(ev.C, incumbent.C)
    nov = novelty(cand.components, incumbent_counts)
    div_pen = diversity_penalty(cand.components, incumbent_counts)
    d = Decision(cand.variant, False, "", S=ev.S, C=ev.C, delta_S=dS, delta_C=dC,
                 novelty=nov, guards=list(guards or []))
    floor = S_star - delta
    if ev.S < floor:
        d.reason = (f"below noise-adjusted floor: S' {ev.S:.4f} < S* {S_star:.4f} "
                    f"- delta {delta:.4f}")
        return d
    ok, why = cost_rule(dS, dC, nov, delta, cfg, div_pen)
    if not ok:
        d.reason = f"cost rule failed: {why}"
        return d
    if guards:
        d.reason = "domain guard violated: " + "; ".join(guards)
        return d
    d.admissible = True
    d.reason = f"admissible: {why}"
    return d


def select_round(cands: list[Candidate], incumbent: EvalResult, S_star: float,
                 delta: float, cfg, incumbent_counts: dict,
                 guard_fn=None) -> tuple[Candidate | None, list[Decision]]:
    """Judge every candidate, return (winner or None, decisions)."""
    decisions = []
    for c in cands:
        g = guard_fn(incumbent, c.ev) if (guard_fn and c.ev is not None) else []
        decisions.append(judge(c, incumbent, S_star, delta, cfg,
                               incumbent_counts, g))
    adm = [(c, d) for c, d in zip(cands, decisions) if d.admissible]
    if not adm:
        return None, decisions
    winner, _ = max(adm, key=lambda cd: cd[1].S)
    return winner, decisions
