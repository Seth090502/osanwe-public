"""Fixed, complete synthetic development comparison; never an alpha certificate.

Run only with a preregistered plan and a new output directory. The caller should
copy this module and numerical dependencies into a disposable sandbox first.
No existing market database or locked holdout is used. No candidate callbacks.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

import numpy as np
import scipy

from allocation import optimize_allocation
from covariance import estimate_covariance
from tournament_runner import simulate_target_weights


METHODS = ("sample", "oas", "ewma", "qis")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def covariance_case(n, p, regime, rng):
    """Known truth from prespecified stationary/heavy-tail/change generators."""
    if regime == "identity":
        truth = np.eye(p)
    elif regime == "heterogeneous":
        truth = np.diag(np.geomspace(.25, 4., p))
    elif regime == "spiked":
        q, _ = np.linalg.qr(rng.normal(size=(p, p)))
        eig = np.ones(p); eig[0] = 10; eig[1] = 3
        truth = (q * eig) @ q.T
    elif regime == "heavy_tail":
        vol = np.linspace(.5, 2., p)
        truth = (.35 * np.ones((p,p)) + .65 * np.eye(p)) * np.outer(vol,vol)
    elif regime == "regime_change":
        truth = 4 * (.8 * np.ones((p,p)) + .2 * np.eye(p))
    else:
        raise ValueError("unregistered covariance regime")
    truth *= 1e-4
    z = rng.normal(size=(n, p))
    if regime == "heavy_tail":
        z *= np.sqrt(3 / rng.chisquare(5, size=n))[:,None]
    x = z @ np.linalg.cholesky(truth).T
    if regime == "regime_change":
        cutoff = 3*n//4
        old = 1e-4 * (.1 * np.ones((p,p)) + .9 * np.eye(p))
        x[:cutoff] = z[:cutoff] @ np.linalg.cholesky(old).T
    return x, truth


def covariance_benchmark(plan):
    cfg = plan["covariance_cases"]
    rows, paired = [], {m: [] for m in METHODS}
    for dim_i, (n, p) in enumerate(cfg["dimensions"]):
        for reg_i, regime in enumerate(cfg["regimes"]):
            cell = {m: [] for m in METHODS}
            for replicate in range(cfg["replicates"]):
                rng = np.random.default_rng(np.random.SeedSequence([cfg["seed"],dim_i,reg_i,replicate]))
                try:
                    x, truth = covariance_case(n,p,regime,rng)
                except Exception as exc:
                    for method in METHODS:
                        rows.append(dict(n=n,p=p,regime=regime,replicate=replicate,method=method,
                                         status="failed",reason="generator: "+str(exc)))
                    continue
                losses = {}
                for method in METHODS:
                    try:
                        args = dict(method=method, annualization=1)
                        if method == "ewma":
                            args["decay"] = plan["ewma_decay"]
                        result = estimate_covariance(x, **args)
                        estimate = np.asarray(result["covariance"], dtype=float)
                        if estimate.shape != truth.shape or not np.isfinite(estimate).all():
                            raise ValueError("invalid covariance output")
                        loss = float(np.sum((estimate-truth)**2) / np.sum(truth**2))
                        if not math.isfinite(loss) or loss<0:
                            raise ValueError("nonfinite or negative estimation loss")
                        losses[method] = loss
                        cell[method].append(loss)
                        rows.append(dict(n=n,p=p,regime=regime,replicate=replicate,
                                         method=method,status="evaluated",relative_frobenius_loss=loss))
                    except Exception as exc:
                        rows.append(dict(n=n,p=p,regime=regime,replicate=replicate,
                                         method=method,status="failed",reason=type(exc).__name__+": "+str(exc)))
                if len(losses)==len(METHODS):
                    for m in METHODS:
                        paired[m].append((losses["sample"],losses[m]))
    summaries=[]
    for m in METHODS:
        values=np.array(paired[m])
        failures=sum(r["status"]=="failed" and r["method"]==m for r in rows)
        cfg_comp=plan["comparisons"]
        rng=np.random.default_rng(cfg_comp["bootstrap_seed"])
        boot=[]
        required_cases=len(cfg["dimensions"])*len(cfg["regimes"])*cfg["replicates"]
        if len(values)==required_cases:
            strata=values.reshape(-1,cfg["replicates"],2)
            for _ in range(cfg_comp["bootstrap_draws"]):
                indices=rng.integers(0,cfg["replicates"],(len(strata),cfg["replicates"]))
                sample=strata[np.arange(len(strata))[:,None],indices]
                boot.append(1-float(sample[:,:,1].mean()/sample[:,:,0].mean()))
            alpha=(1-cfg_comp["confidence"])/2
            ci=np.quantile(boot,[alpha,1-alpha]).tolist()
            reduction=1-float(values[:,1].mean()/values[:,0].mean())
        else:
            ci=None;reduction=None
        total_failures=sum(r["status"]=="failed" for r in rows)
        claim=(m!="sample" and total_failures==0 and ci is not None and ci[0]>0
               and reduction>=cfg_comp["minimum_relative_error_reduction"])
        summaries.append(dict(method=m,failures=failures,complete_paired_cases=len(values),
                              relative_error_reduction_vs_sample=reduction,
                              paired_bootstrap_interval=ci,confidence=cfg_comp["confidence"],
                              registered_synthetic_improvement_criterion_passed=claim))
    # Per-cell reporting prevents a pooled result from hiding losing regimes.
    cells=[]
    for n,p in cfg["dimensions"]:
        for regime in cfg["regimes"]:
            for method in METHODS:
                subset=[r for r in rows if (r["n"],r["p"],r["regime"],r["method"])==(n,p,regime,method)]
                good=[r["relative_frobenius_loss"] for r in subset if r["status"]=="evaluated"]
                cells.append(dict(n=n,p=p,regime=regime,method=method,count=len(good),
                                  failures=len(subset)-len(good),mean_loss=float(np.mean(good)) if good else None))
    return dict(rows=rows,cells=cells,comparisons=summaries,
                inference_scope="paired within-stratum replicate bootstrap; equal fixed-cell weighting, Bonferroni-adjusted intervals; approximate synthetic inference only")


def price_case(cfg, regime, seed):
    rng=np.random.default_rng(seed)
    p=cfg["assets"];n=cfg["observations"]
    base=(.25*np.ones((p,p))+.75*np.eye(p))*np.outer(np.linspace(.008,.02,p),np.linspace(.008,.02,p))
    z=rng.normal(size=(n-1,p))
    if regime=="heavy_tail":
        z*=np.sqrt(3/rng.chisquare(5,size=n-1))[:,None]
    rets=z@np.linalg.cholesky(base).T
    if regime=="regime_change":
        after=(.8*np.ones((p,p))+.2*np.eye(p))*.0006
        rets[n//2:]=z[n//2:]@np.linalg.cholesky(after).T
    if np.any(rets<=-1):
        raise ValueError("synthetic price generator produced nonpositive price; do not clip/resample")
    prices=np.vstack([np.ones(p)*100,100*np.cumprod(1+rets,axis=0)])
    dates=[];d=date(2020,1,2)
    while len(dates)<n:
        if d.weekday()<5:dates.append(d.isoformat())
        d+=timedelta(days=1)
    symbols=["A%02d"%i for i in range(p)]
    px={s:dict(zip(dates,prices[:,j].tolist())) for j,s in enumerate(symbols)}
    return dates,symbols,px,rets


def _book_metrics(book):
    r=np.array(list(book["returns"].values()),dtype=float)
    equity=np.array(list(book["equity"].values()),dtype=float)
    path=np.r_[1.,equity]
    drawdown=path/np.maximum.accumulate(path)-1
    return dict(net_return=float(path[-1]-1),annualized_volatility=float(np.std(r,ddof=1)*np.sqrt(252)),
                max_drawdown=float(drawdown.min()),transaction_cost=book["total_cost"],
                turnover_l1=book["one_way_turnover"])


def portfolio_benchmark(plan):
    cfg=plan["portfolio_cases"];rows=[]
    for regime in cfg["regimes"]:
        for seed in cfg["seeds"]:
            try:
                dates,symbols,px,rets=price_case(cfg,regime,seed)
            except Exception as exc:
                for bps in cfg["one_way_cost_bps"]:
                    for method in cfg["candidates"]:
                        rows.append(dict(regime=regime,seed=seed,one_way_cost_bps=bps,method=method,
                                         status="failed",reason="generator: "+str(exc)))
                continue
            start=cfg["lookback"]
            for bps in cfg["one_way_cost_bps"]:
                for method in cfg["candidates"]:
                    label=dict(regime=regime,seed=seed,one_way_cost_bps=bps,method=method)
                    try:
                        targets={};calendar=dates[start:]
                        if method=="equal_weight_buy_hold":
                            # Same first decision/fill timing as every fitted method.
                            targets[dates[start]]={s:1/len(symbols) for s in symbols}
                        else:
                            for t in range(start,len(dates)-1,cfg["rebalance_every"]):
                                history=rets[t-cfg["lookback"]:t]
                                args=dict(method=method,annualization=1)
                                if method=="ewma":args["decay"]=plan["ewma_decay"]
                                cov=estimate_covariance(history,**args)["covariance"]
                                if targets:
                                    prefix=simulate_target_weights(px,dates[start:t+1],targets,
                                                                  one_way_cost_bps=bps,liquidate_final=False)
                                    nav=prefix["equity"][dates[t]]
                                    current=[prefix["positions"][dates[t]].get(s,0)/nav for s in symbols]
                                else:current=[0.]*len(symbols)
                                # Asset-specific research cost penalties are explicit; execution stress cost is separate.
                                costs=np.linspace(.75,1.25,len(symbols))*bps/10000
                                out=optimize_allocation(cov,current_weights=current,one_way_costs=costs,
                                                        risk_aversion=cfg["risk_aversion"],
                                                        horizon_periods=cfg["rebalance_every"] ,max_weight=cfg["max_weight"])
                                targets[dates[t]]=dict(zip(symbols,out["weights"]))
                        book=simulate_target_weights(px,calendar,targets,one_way_cost_bps=bps,liquidate_final=True)
                        label.update(status="evaluated",**_book_metrics(book))
                    except Exception as exc:
                        label.update(status="failed",reason=type(exc).__name__+": "+str(exc))
                    rows.append(label)
    return dict(rows=rows,ranking="none; all fixed risk/cost cases reported, no Sharpe/alpha selection")


def validate_plan(plan):
    if tuple(plan["methods"])!=METHODS or len(set(plan["portfolio_cases"]["candidates"]))!=5:
        raise ValueError("complete fixed methods required")
    if set(plan["portfolio_cases"]["candidates"])!={"equal_weight_buy_hold",*METHODS}:
        raise ValueError("baseline/candidate omitted")
    if plan["ewma_decay"]!=.94:
        raise ValueError("unregistered EWMA decay")
    c=plan["covariance_cases"];p=plan["portfolio_cases"]
    if (set(c["regimes"])!={"identity","heterogeneous","spiked","heavy_tail","regime_change"}
            or len(c["regimes"])!=5 or not c["dimensions"]):
        raise ValueError("complete nonempty covariance regimes/dimensions required")
    def integer(v,minimum):return isinstance(v,int) and not isinstance(v,bool) and v>=minimum
    if (not integer(c["replicates"],2) or any(len(d)!=2 or not all(integer(v,2) for v in d) for d in c["dimensions"])
            or len({tuple(d) for d in c["dimensions"]})!=len(c["dimensions"])):
        raise ValueError("invalid or duplicate covariance cases")
    if (set(p["regimes"])!={"stationary","heavy_tail","regime_change"} or len(p["regimes"])!=3
            or not p["seeds"] or len(set(p["seeds"]))!=len(p["seeds"])
            or not all(integer(s,0) for s in p["seeds"]) or not p["one_way_cost_bps"]
            or len(set(p["one_way_cost_bps"]))!=len(p["one_way_cost_bps"])):
        raise ValueError("complete nonempty portfolio scenario matrix required")
    if (not integer(p["assets"],3) or not integer(p["lookback"],3)
            or not integer(p["observations"],p["lookback"]+3) or not integer(p["rebalance_every"],1)):
        raise ValueError("invalid portfolio dimensions")
    comp=plan["comparisons"]
    if (not integer(comp["bootstrap_draws"],1000) or not .9<comp["confidence"]<1
            or not 0<comp["minimum_relative_error_reduction"]<1):
        raise ValueError("invalid statistical protocol")


def install_sandbox_guard(root):
    """Defense in depth for trusted local numerical code; not OS containment."""
    root=Path(root).resolve()
    def guard(event,args):
        if event in {"socket.connect","socket.bind","subprocess.Popen","os.system"}:
            raise PermissionError("sandbox forbids network/process actions")
        if event=="open" and isinstance(args[0],(str,bytes)):
            p=Path(args[0]).resolve()
            if not p.is_relative_to(root):
                raise PermissionError("sandbox file access outside disposable root")
    sys.addaudithook(guard)


def complete_case_matrix(plan, result):
    """No empty, duplicated, missing, extra or failed case can certify a run."""
    c=plan["covariance_cases"];p=plan["portfolio_cases"]
    expected_c={(n,k,regime,rep,m) for n,k in c["dimensions"] for regime in c["regimes"]
                for rep in range(c["replicates"]) for m in METHODS}
    expected_p={(regime,seed,bps,m) for regime in p["regimes"] for seed in p["seeds"]
                for bps in p["one_way_cost_bps"] for m in p["candidates"]}
    cr=result["covariance"]["rows"];pr=result["portfolio"]["rows"]
    actual_c={(r["n"],r["p"],r["regime"],r["replicate"],r["method"]) for r in cr}
    actual_p={(r["regime"],r["seed"],r["one_way_cost_bps"],r["method"]) for r in pr}
    return bool(expected_c and expected_p and actual_c==expected_c and actual_p==expected_p
                and len(cr)==len(expected_c) and len(pr)==len(expected_p)
                and all(r["status"]=="evaluated" for r in cr+pr))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan",required=True)
    ap.add_argument("--plan-sha256",required=True)
    ap.add_argument("--output-dir",required=True)
    args=ap.parse_args()
    source_dir=Path(__file__).resolve().parent
    temp_root=Path(tempfile.gettempdir()).resolve()
    plan_path=Path(args.plan).resolve();out=Path(args.output_dir).resolve()
    if (source_dir==temp_root or not source_dir.is_relative_to(temp_root)
            or not plan_path.is_relative_to(source_dir) or not out.is_relative_to(source_dir)):
        raise ValueError("copy trusted code/plan into a disposable OS temporary directory; output must stay inside it")
    if digest(plan_path)!=args.plan_sha256:
        raise ValueError("preregistration digest mismatch")
    plan=json.loads(plan_path.read_text(encoding="utf-8"));validate_plan(plan)
    out.mkdir(exist_ok=False)
    pins={p.name:digest(p) for p in source_dir.glob("*.py")}
    start=datetime.now(timezone.utc).isoformat()
    install_sandbox_guard(source_dir)
    result=dict(protocol_id=plan["protocol_id"],plan_sha256=args.plan_sha256,source_sha256=pins,
                started_at=start,runtime=dict(python=sys.version,numpy=np.__version__,scipy=scipy.__version__),
                scope=plan["scope"],limitations=plan["limits"],novel_method=plan["novel_method"],
                covariance=covariance_benchmark(plan),portfolio=portfolio_benchmark(plan),
                finished_at=datetime.now(timezone.utc).isoformat())
    result["complete"]=complete_case_matrix(plan,result)
    result["source_unchanged"]=pins=={p.name:digest(p) for p in source_dir.glob("*.py")}
    (out/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="ascii")
    print(json.dumps(dict(complete=result["complete"],source_unchanged=result["source_unchanged"],
                         covariance_cases=len(result["covariance"]["rows"]),portfolio_cases=len(result["portfolio"]["rows"]))))
    return 0 if result["complete"] and result["source_unchanged"] else 1


if __name__=="__main__":
    raise SystemExit(main())
