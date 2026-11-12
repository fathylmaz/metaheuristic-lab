import { useEffect, useMemo, useRef, useState } from 'react';
import type { Frame, Run } from '../lib/types';
import { objectiveValue, numberFmt } from '../lib/math';

type Props = { run: Run | null; frame: Frame | null; objective: string; selectedId: number | null; setSelectedId: (id: number | null) => void; trails: boolean; showTargets: boolean };

export default function Landscape({ run, frame, objective, selectedId, setSelectedId, trails, showTargets }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wrapRef = useRef<HTMLDivElement>(null);
  const [size, setSize] = useState({ width: 700, height: 470 });
  const bounds = useMemo<[number,number]>(() => run?.bounds ?? [-5.12, 5.12], [run]);
  const bg = useMemo(() => {
    const c = document.createElement('canvas'); c.width = 300; c.height = 300;
    const cx = c.getContext('2d')!;
    const image = cx.createImageData(c.width, c.height);
    const vals: number[] = [];
    for (let y=0;y<c.height;y++) for(let x=0;x<c.width;x++) {
      const px = bounds[0] + x/(c.width-1)*(bounds[1]-bounds[0]);
      const py = bounds[1] - y/(c.height-1)*(bounds[1]-bounds[0]);
      vals.push(objectiveValue(objective,px,py));
    }
    const sorted = [...vals].sort((a,b)=>a-b);
    const low = sorted[Math.floor(sorted.length*.03)] || 0;
    const high = sorted[Math.floor(sorted.length*.96)] || 1;
    vals.forEach((v,idx)=>{
      const t = Math.min(1,Math.max(0,(v-low)/(high-low||1)));
      const band = Math.pow(t,.65);
      const p=idx*4;
      image.data[p]=Math.round(12+37*band);
      image.data[p+1]=Math.round(37+47*(1-band));
      image.data[p+2]=Math.round(51+42*(1-band));
      image.data[p+3]=255;
    });
    cx.putImageData(image,0,0);
    return c;
  }, [objective,bounds]);
  useEffect(()=>{
    const observer = new ResizeObserver(entries=>{
      const w=entries[0].contentRect.width;
      setSize({width:w,height:Math.max(320,Math.min(535,w*.68))});
    });
    if(wrapRef.current) observer.observe(wrapRef.current);
    return ()=>observer.disconnect();
  },[]);
  useEffect(()=>{
    const canvas=canvasRef.current;
    if(!canvas) return;
    const dpr=Math.min(window.devicePixelRatio || 1,2);
    canvas.width=Math.floor(size.width*dpr);
    canvas.height=Math.floor(size.height*dpr);
    const ctx=canvas.getContext('2d')!;
    ctx.scale(dpr,dpr);
    const w=size.width,h=size.height;
    const pad={left:44,right:24,top:24,bottom:36};
    const pw=w-pad.left-pad.right, ph=h-pad.top-pad.bottom;
    const px=(x:number)=>pad.left+(x-bounds[0])/(bounds[1]-bounds[0])*pw;
    const py=(y:number)=>pad.top+(bounds[1]-y)/(bounds[1]-bounds[0])*ph;
    ctx.fillStyle='#0a1720';ctx.fillRect(0,0,w,h);
    ctx.globalAlpha=.95;ctx.drawImage(bg,pad.left,pad.top,pw,ph);ctx.globalAlpha=1;
    ctx.strokeStyle='rgba(197,220,229,.115)';ctx.lineWidth=1;
    for(let i=0;i<=8;i++){
      const vx=pad.left+pw*i/8,vy=pad.top+ph*i/8;
      ctx.beginPath();ctx.moveTo(vx,pad.top);ctx.lineTo(vx,pad.top+ph);ctx.stroke();
      ctx.beginPath();ctx.moveTo(pad.left,vy);ctx.lineTo(pad.left+pw,vy);ctx.stroke();
    }
    ctx.strokeStyle='rgba(162,209,213,.35)';ctx.strokeRect(pad.left,pad.top,pw,ph);
    ctx.fillStyle='#90a7b2';ctx.font='11px Inter,system-ui';
    for(let i=0;i<=4;i++){
      const value=bounds[0]+i/4*(bounds[1]-bounds[0]);
      ctx.fillText(value.toFixed(1),pad.left+pw*i/4-12,h-13);
      const yValue=bounds[1]-i/4*(bounds[1]-bounds[0]);
      ctx.fillText(yValue.toFixed(1),5,pad.top+ph*i/4+4);
    }
    if(run && frame){
      const isPso=run.algorithm==='pso';
      const isAbc=run.algorithm==='abc';
      const isCs=run.algorithm==='cs';
      const isMfo=run.algorithm==='mfo';
      const isGwo=run.algorithm==='gwo';
      const isWoa=run.algorithm==='woa';
      const isBa=run.algorithm==='ba';
      const isSsa=run.algorithm==='ssa';
      const isSma=run.algorithm==='sma';
      const isIwo=run.algorithm==='iwo';
      const isSa=run.algorithm==='sa';
      const isGsa=run.algorithm==='gsa';
      const isDe=run.algorithm==='de';
      if(trails && !isIwo){
        const start=Math.max(0,frame.iteration-16);
        for(const agent of frame.agents){
          ctx.beginPath();
          for(let it=start;it<=frame.iteration;it++){
            const p=run.frames[it].agents[agent.id];
            if(it===start) ctx.moveTo(px(p.x),py(p.y));else ctx.lineTo(px(p.x),py(p.y));
          }
          ctx.strokeStyle=agent.id===selectedId?'rgba(125,243,220,.8)':(isPso?'rgba(96,193,255,.23)':isAbc?'rgba(173,230,146,.25)':isCs?'rgba(231,187,126,.32)':isMfo?'rgba(222,168,250,.27)':isGwo?'rgba(120,230,186,.22)':isWoa?'rgba(102,188,242,.27)':isBa?'rgba(205,145,250,.28)':isSsa?'rgba(117,239,205,.30)':isSma?'rgba(188,236,164,.28)':'rgba(244,179,88,.22)');
          ctx.lineWidth=agent.id===selectedId?2:1;ctx.stroke();
        }
      }
      const selected=frame.agents.find(a=>a.id===selectedId);
      const target=selected?.target_id==null?null:frame.agents[selected.target_id];
      if(showTargets && selected && target && !isPso && !isWoa && !isBa && !isSsa && !isGsa){
        ctx.strokeStyle='rgba(113,238,212,.7)';ctx.lineWidth=1.5;ctx.setLineDash([6,5]);
        ctx.beginPath();ctx.moveTo(px(selected.x),py(selected.y));ctx.lineTo(px(target.x),py(target.y));ctx.stroke();ctx.setLineDash([]);
      }
      if(isDe && showTargets && frame.iteration>0){
        const individual=frame.agents.find(a=>a.id===selectedId);
        if(individual?.de_parent && individual.de_donor_positions && individual.de_mutant && individual.de_trial){
          const parent=individual.de_parent;
          const [r1,r2,r3]=individual.de_donor_positions;
          const mutant=individual.de_mutant;
          const trial=individual.de_trial;
          const lines:[number[],number[],string,number][]=[
            [r2,r3,'#91c4ff',1.8], [r1,mutant,'#d6acff',2.2],
            [parent,trial,individual.de_accepted?'#8ff3bd':'#efa381',2.4],
          ];
          for(const [start,end,color,width] of lines){
            ctx.strokeStyle=color;ctx.lineWidth=width;ctx.setLineDash([6,4]);
            ctx.beginPath();ctx.moveTo(px(start[0]),py(start[1]));ctx.lineTo(px(end[0]),py(end[1]));ctx.stroke();
          }
          ctx.setLineDash([]);
          [r1,r2,r3].forEach((donor,i)=>{
            ctx.strokeStyle=['#ffd292','#90cafa','#f3b0cc'][i];ctx.lineWidth=2;
            ctx.beginPath();ctx.arc(px(donor[0]),py(donor[1]),7,0,Math.PI*2);ctx.stroke();
            ctx.font='bold 11px system-ui';ctx.fillStyle=ctx.strokeStyle;
            ctx.fillText(`r${i+1}`,px(donor[0])+8,py(donor[1])-8);
          });
          ctx.strokeStyle='#d7b4ff';ctx.lineWidth=2;
          ctx.beginPath();ctx.rect(px(mutant[0])-5,py(mutant[1])-5,10,10);ctx.stroke();
          ctx.strokeStyle=individual.de_accepted?'#91ffc0':'#f5a086';ctx.lineWidth=2;
          ctx.beginPath();ctx.arc(px(trial[0]),py(trial[1]),8,0,Math.PI*2);ctx.stroke();
          if(!individual.de_accepted){
            ctx.beginPath();ctx.moveTo(px(trial[0])-5,py(trial[1])-5);ctx.lineTo(px(trial[0])+5,py(trial[1])+5);
            ctx.moveTo(px(trial[0])+5,py(trial[1])-5);ctx.lineTo(px(trial[0])-5,py(trial[1])+5);ctx.stroke();
          }
        }
      }
      if(isGsa && showTargets && frame.iteration>0){
        // Display source-generation dominant attraction and correctly scaled direction.
        // This line does not claim to be the whole Newtonian force sum.
        const chosen=frame.agents.find(a=>a.id===selectedId);
        if(chosen?.gsa_previous && chosen.gsa_force){
          const [ox,oy]=chosen.gsa_previous;
          if(chosen.gsa_attractor){
            const [tx,ty]=chosen.gsa_attractor;
            ctx.strokeStyle='rgba(112,222,249,.80)';ctx.lineWidth=1.4;ctx.setLineDash([5,4]);
            ctx.beginPath();ctx.moveTo(px(ox),py(oy));ctx.lineTo(px(tx),py(ty));ctx.stroke();ctx.setLineDash([]);
            ctx.beginPath();ctx.arc(px(tx),py(ty),8,0,2*Math.PI);ctx.stroke();
          }
          const force=chosen.gsa_force;
          const norm=Math.hypot(force[0],force[1]);
          if(norm>1e-18){
            const length=Math.min(43,14+Math.log1p(norm)*8);
            const ex=px(ox)+force[0]/norm*length, ey=py(oy)-force[1]/norm*length;
            ctx.strokeStyle='#ffd18c';ctx.fillStyle='#ffd18c';ctx.lineWidth=2.2;
            ctx.beginPath();ctx.moveTo(px(ox),py(oy));ctx.lineTo(ex,ey);ctx.stroke();
            const a=Math.atan2(ey-py(oy),ex-px(ox));
            ctx.beginPath();ctx.moveTo(ex,ey);ctx.lineTo(ex-8*Math.cos(a-.45),ey-8*Math.sin(a-.45));ctx.lineTo(ex-8*Math.cos(a+.45),ey-8*Math.sin(a+.45));ctx.closePath();ctx.fill();
          }
        }
      }
      if(isSa && showTargets && frame.iteration > 0){
        const a=frame.agents[0];
        if(a?.sa_previous && a.sa_candidate){
          const [ox,oy]=a.sa_previous,[cx,cy]=a.sa_candidate;
          const color=a.sa_accepted?'#9cefb9':'#f1a078';
          ctx.strokeStyle=color;ctx.lineWidth=2;ctx.setLineDash([6,4]);
          ctx.beginPath();ctx.moveTo(px(ox),py(oy));ctx.lineTo(px(cx),py(cy));ctx.stroke();ctx.setLineDash([]);
          ctx.beginPath();ctx.arc(px(cx),py(cy),a.sa_accepted?7:9,0,2*Math.PI);ctx.stroke();
          if(!a.sa_accepted){
            ctx.beginPath();ctx.moveTo(px(cx)-5,py(cy)-5);ctx.lineTo(px(cx)+5,py(cy)+5);
            ctx.moveTo(px(cx)+5,py(cy)-5);ctx.lineTo(px(cx)-5,py(cy)+5);ctx.stroke();
          }
        }
      }
      if(isSma && showTargets && frame.iteration > 0){
        // Actual frozen source coordinates, archive anchor and position for the selected step.
        const slime=frame.agents.find(agent=>agent.id===selectedId);
        if(slime?.sma_previous){
          const prev=slime.sma_previous;
          const best=slime.sma_best_reference;
          const color=slime.sma_move_kind==='restart'?'#a5f4a4':slime.sma_move_kind==='approach'?'#f7ce8b':'#83dbe8';
          ctx.strokeStyle=color;ctx.lineWidth=2.2;ctx.setLineDash([6,4]);
          ctx.beginPath();ctx.moveTo(px(prev[0]),py(prev[1]));ctx.lineTo(px(slime.x),py(slime.y));ctx.stroke();ctx.setLineDash([]);
          ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();ctx.arc(px(prev[0]),py(prev[1]),6,0,Math.PI*2);ctx.stroke();
          if(best){
            ctx.strokeStyle='rgba(242,214,152,.85)';ctx.lineWidth=1.5;
            ctx.beginPath();ctx.arc(px(best[0]),py(best[1]),9,0,Math.PI*2);ctx.stroke();
          }
          if(slime.sma_move_kind==='approach'){
            [slime.sma_source_a_position,slime.sma_source_b_position].forEach((point,k)=>{
              if(!point)return;
              ctx.strokeStyle=k===0?'#9cefc6':'#d6b1f4';ctx.lineWidth=1.7;ctx.setLineDash([3,5]);
              ctx.beginPath();ctx.moveTo(px(slime.x),py(slime.y));ctx.lineTo(px(point[0]),py(point[1]));ctx.stroke();ctx.setLineDash([]);
              ctx.beginPath();ctx.arc(px(point[0]),py(point[1]),6,0,Math.PI*2);ctx.stroke();
            });
          }
        }
      }
      if(isSsa && showTargets){
        // Ordered chain: connect each evaluated NEW salp to its NEW predecessor.
        ctx.setLineDash([]);
        ctx.lineWidth=1.4;
        for(let i=1;i<frame.agents.length;i++){
          const a=frame.agents[i], predecessor=frame.agents[i-1];
          ctx.strokeStyle=i===selectedId || i-1===selectedId?'rgba(150,255,222,.98)':'rgba(104,231,187,.42)';
          ctx.lineWidth=i===selectedId || i-1===selectedId?2.4:1.1;
          ctx.beginPath();ctx.moveTo(px(predecessor.x),py(predecessor.y));ctx.lineTo(px(a.x),py(a.y));ctx.stroke();
        }
        const leader=frame.agents[0], food=frame.ssa_food_position;
        if(food){
          ctx.strokeStyle='rgba(255,194,115,.85)';ctx.lineWidth=2;
          ctx.setLineDash([6,4]);ctx.beginPath();ctx.moveTo(px(leader.x),py(leader.y));ctx.lineTo(px(food[0]),py(food[1]));ctx.stroke();ctx.setLineDash([]);
          ctx.beginPath();ctx.arc(px(food[0]),py(food[1]),8,0,2*Math.PI);ctx.stroke();
        }
        if(selected?.ssa_previous && selected?.ssa_target){
          const [ox,oy]=selected.ssa_previous;
          const [tx,ty]=selected.ssa_target;
          ctx.strokeStyle='rgba(242,177,117,.9)';ctx.lineWidth=1.6;
          ctx.setLineDash([3,4]);ctx.beginPath();ctx.moveTo(px(ox),py(oy));ctx.lineTo(px(tx),py(ty));ctx.stroke();ctx.setLineDash([]);
          ctx.beginPath();ctx.arc(px(ox),py(oy),6,0,2*Math.PI);ctx.stroke();
        }
      }
      if(isPso && showTargets){
        // Velocity vectors: true recorded velocities, not decorative animation.
        for(const a of frame.agents){
          const vx=a.vx??0,vy=a.vy??0;
          const startX=px(a.x),startY=py(a.y);
          const endX=px(Math.max(bounds[0],Math.min(bounds[1],a.x+vx*.65)));
          const endY=py(Math.max(bounds[0],Math.min(bounds[1],a.y+vy*.65)));
          const len=Math.hypot(endX-startX,endY-startY);
          if(len<2) continue;
          const angle=Math.atan2(endY-startY,endX-startX);
          const active=a.id===selectedId;
          ctx.strokeStyle=active?'rgba(137,255,229,.95)':'rgba(109,189,255,.45)';
          ctx.lineWidth=active?2.1:1.1;
          ctx.beginPath();ctx.moveTo(startX,startY);ctx.lineTo(endX,endY);ctx.stroke();
          ctx.beginPath();ctx.moveTo(endX,endY);
          ctx.lineTo(endX-5*Math.cos(angle-.55),endY-5*Math.sin(angle-.55));
          ctx.moveTo(endX,endY);ctx.lineTo(endX-5*Math.cos(angle+.55),endY-5*Math.sin(angle+.55));ctx.stroke();
        }
        if(selected){
          if(selected.pbest_x!=null && selected.pbest_y!=null){
            ctx.setLineDash([4,5]);ctx.strokeStyle='rgba(245,175,93,.75)';ctx.lineWidth=1.4;
            ctx.beginPath();ctx.moveTo(px(selected.x),py(selected.y));ctx.lineTo(px(selected.pbest_x),py(selected.pbest_y));ctx.stroke();ctx.setLineDash([]);
            ctx.beginPath();ctx.arc(px(selected.pbest_x),py(selected.pbest_y),7,0,Math.PI*2);ctx.stroke();
          }
          ctx.setLineDash([6,4]);ctx.strokeStyle='rgba(125,243,220,.8)';ctx.lineWidth=1.4;
          ctx.beginPath();ctx.moveTo(px(selected.x),py(selected.y));ctx.lineTo(px(frame.best_position[0]),py(frame.best_position[1]));ctx.stroke();ctx.setLineDash([]);
        }
      }
      if(isIwo && frame.iteration>0 && (trails||showTargets)){
        // Population IDs are globally unique, NOT indices. Never index earlier frames
        // by a seed ID: instead draw the recorded actual parent -> surviving child link.
        for(const a of frame.agents){
          if(a.iwo_origin!=='offspring'||!a.iwo_parent_position)continue;
          const parent=a.iwo_parent_position;
          ctx.strokeStyle=a.id===selectedId?'rgba(145,255,214,.95)':'rgba(159,237,140,.38)';
          ctx.lineWidth=a.id===selectedId?2.3:1.0;ctx.setLineDash([4,4]);
          ctx.beginPath();ctx.moveTo(px(parent[0]),py(parent[1]));ctx.lineTo(px(a.x),py(a.y));ctx.stroke();
          if(a.id===selectedId){ctx.setLineDash([]);ctx.strokeStyle='#c4f8a8';ctx.beginPath();ctx.arc(px(parent[0]),py(parent[1]),8,0,Math.PI*2);ctx.stroke();}
        }
        ctx.setLineDash([]);
      }
      if(isCs && showTargets && frame.iteration>0){
        const previous=run.frames[frame.iteration-1];
        for(const a of frame.agents){
          if(a.move_kind==='retained') continue;
          const old=previous.agents[a.id];
          const changed=Math.hypot(a.x-old.x,a.y-old.y)>1e-10;
          if(!changed) continue;
          ctx.strokeStyle=a.move_kind==='abandoned'?'rgba(169,243,150,.60)':'rgba(255,187,106,.70)';
          ctx.lineWidth=a.id===selectedId?2.3:1.2;
          ctx.setLineDash(a.move_kind==='abandoned'?[2,5]:[7,4]);
          ctx.beginPath();ctx.moveTo(px(old.x),py(old.y));ctx.lineTo(px(a.x),py(a.y));ctx.stroke();
        }
        ctx.setLineDash([]);
      }
      if(isMfo && showTargets){
        // These are actual flames used for THIS update; not decorative points.
        const uniqueFlames = new Map<number,[number,number]>();
        for(const a of frame.agents){
          if(a.flame_x==null || a.flame_y==null || a.flame_rank==null)continue;
          uniqueFlames.set(a.flame_rank,[a.flame_x,a.flame_y]);
          ctx.strokeStyle=a.id===selectedId?'rgba(248,210,139,.94)':'rgba(184,137,240,.14)';
          ctx.lineWidth=a.id===selectedId?2.0:.75;
          ctx.setLineDash(a.id===selectedId?[5,4]:[3,7]);
          ctx.beginPath();ctx.moveTo(px(a.x),py(a.y));ctx.lineTo(px(a.flame_x),py(a.flame_y));ctx.stroke();
        }
        ctx.setLineDash([]);
        for(const [rank,point] of uniqueFlames){
          const fx=px(point[0]),fy=py(point[1]);
          ctx.strokeStyle=rank===0?'#ffca88':'rgba(206,153,255,.84)';
          ctx.lineWidth=rank===0?2:1.3;
          ctx.beginPath();ctx.moveTo(fx,fy-8);ctx.lineTo(fx+6,fy);ctx.lineTo(fx,fy+8);ctx.lineTo(fx-6,fy);ctx.closePath();ctx.stroke();
        }
      }
      if(isBa && showTargets && frame.iteration>0){
        const bat=frame.agents.find(a=>a.id===selectedId);
        if(bat?.ba_previous && bat.ba_candidate){
          const [ox,oy]=bat.ba_previous, [cx,cy]=bat.ba_candidate;
          const color=bat.ba_accepted?'#98f4bf':'#ee9d7e';
          // The dashed line shows the ACTUAL evaluated candidate, not an imaginary accepted path.
          ctx.strokeStyle=color;ctx.lineWidth=2;ctx.setLineDash([5,5]);
          ctx.beginPath();ctx.moveTo(px(ox),py(oy));ctx.lineTo(px(cx),py(cy));ctx.stroke();ctx.setLineDash([]);
          ctx.strokeStyle=color;ctx.lineWidth=2;
          ctx.beginPath();ctx.arc(px(cx),py(cy),8,0,2*Math.PI);ctx.stroke();
          if(!bat.ba_accepted){
            ctx.beginPath();ctx.moveTo(px(cx)-5,py(cy)-5);ctx.lineTo(px(cx)+5,py(cy)+5);
            ctx.moveTo(px(cx)+5,py(cy)-5);ctx.lineTo(px(cx)-5,py(cy)+5);ctx.stroke();
          }
          if(bat.ba_reference_best){
            const [bx,by]=bat.ba_reference_best;
            ctx.strokeStyle='rgba(172,141,255,.8)';ctx.lineWidth=1.5;
            ctx.beginPath();ctx.arc(px(bx),py(by),12,0,2*Math.PI);ctx.stroke();
            if(bat.ba_move_kind==='local'){
              ctx.setLineDash([2,5]);ctx.beginPath();ctx.moveTo(px(bx),py(by));ctx.lineTo(px(cx),py(cy));ctx.stroke();ctx.setLineDash([]);
            }
          }
        }
      }
      if(isWoa && showTargets && frame.iteration>0){
        // Previous, target and actual accepted end positions were saved by Python.
        for(const whale of frame.agents){
          const target=whale.woa_target,old=whale.woa_previous;
          if(!target||!old)continue;
          const chosen=selectedId===whale.id;
          if(!chosen)continue;
          const color=whale.woa_move_kind==='search'?'#f3c27b':whale.woa_move_kind==='spiral'?'#c6a1fa':'#7ddbd0';
          ctx.strokeStyle=color;ctx.lineWidth=2;ctx.setLineDash([6,4]);
          ctx.beginPath();ctx.moveTo(px(old[0]),py(old[1]));ctx.lineTo(px(target[0]),py(target[1]));ctx.stroke();
          ctx.setLineDash([]);
          ctx.strokeStyle='rgba(255,255,255,.7)';ctx.lineWidth=1.2;ctx.beginPath();ctx.moveTo(px(old[0]),py(old[1]));ctx.lineTo(px(whale.x),py(whale.y));ctx.stroke();
          ctx.beginPath();ctx.arc(px(old[0]),py(old[1]),5,0,Math.PI*2);ctx.stroke();
          ctx.beginPath();ctx.arc(px(target[0]),py(target[1]),9,0,Math.PI*2);ctx.strokeStyle=color;ctx.lineWidth=2;ctx.stroke();
        }
      }
      if(isGwo && showTargets && frame.gwo_leader_positions){
        // These are actual preceding-population leader anchors used in this update.
        const leaderColors=['#f8c27d','#70deee','#d2a2fb'];
        const selectWolf=frame.agents.find(a=>a.id===selectedId);
        if(selectWolf){
          frame.gwo_leader_positions.forEach((leader,k)=>{
            ctx.setLineDash([k===0?6:3,5]);
            ctx.lineWidth=k===0?2:1.5;ctx.strokeStyle=leaderColors[k];
            ctx.beginPath();ctx.moveTo(px(selectWolf.x),py(selectWolf.y));ctx.lineTo(px(leader[0]),py(leader[1]));ctx.stroke();
          });
          ctx.setLineDash([]);
        }
        frame.gwo_leader_positions.forEach(([lx,ly],k)=>{
          const x=px(lx),y=py(ly);
          ctx.beginPath();ctx.arc(x,y,9-k,0,2*Math.PI);
          ctx.strokeStyle=leaderColors[k];ctx.lineWidth=2;ctx.stroke();
          ctx.fillStyle=leaderColors[k];ctx.font='bold 11px system-ui';
          ctx.fillText(['α','β','δ'][k],x+10,y-8);
        });
      }
      for(const a of frame.agents){
        const x=px(a.x), y=py(a.y),selected=a.id===selectedId;
        const intensity=Math.max(.25,a.brightness);
        const glow=ctx.createRadialGradient(x,y,1,x,y,selected?22:14);
        glow.addColorStop(0,selected?'rgba(130,255,226,.75)':(isPso?`rgba(112,190,255,${.55*intensity})`:isAbc?`rgba(128,236,163,${.62*intensity})`:isCs?`rgba(210,170,250,${.60*intensity})`:isMfo?`rgba(226,175,255,${.60*intensity})`:isGwo?`rgba(110,226,185,${.60*intensity})`:isWoa?`rgba(129,189,250,${.60*intensity})`:isBa?`rgba(205,157,250,${.60*intensity})`:isSsa?`rgba(110,238,186,${.65*intensity})`:isSma?`rgba(174,241,168,${.65*intensity})`:isIwo?`rgba(158,243,142,${.7*intensity})`:isSa?`rgba(242,180,110,${.7*intensity})`:isGsa?`rgba(121,211,250,${.72*intensity})`:`rgba(255,200,108,${.62*intensity})`));
        glow.addColorStop(1,'rgba(236,161,70,0)');
        ctx.fillStyle=glow;ctx.beginPath();ctx.arc(x,y,selected?22:14,0,Math.PI*2);ctx.fill();
        ctx.fillStyle=selected?'#8fffe2':(isPso?'#a8d3ff':isAbc?(a.role==='scout'?'#acf399':a.role==='onlooker'?'#89d4ff':'#ffd18a'):isCs?(a.move_kind==='abandoned'?'#a1f5a0':a.move_kind==='levy'?'#ffc484':'#c8a9fd'):isMfo?'#ddb6ff':isGwo?(a.wolf_role==='alpha'?'#ffd08f':a.wolf_role==='beta'?'#85e8f2':a.wolf_role==='delta'?'#d1a7ff':'#7fdbb3'):isWoa?(a.woa_move_kind==='search'?'#ffd08f':a.woa_move_kind==='spiral'?'#dab4ff':'#8cece0'):isBa?(a.ba_accepted?'#9ff5be':a.ba_move_kind==='local'?'#cda8ff':'#ffbd91'):isSsa?(a.ssa_role==='leader'?'#ffca86':'#85f0c0'):isSma?(a.sma_move_kind==='restart'?'#a7f3a8':a.sma_move_kind==='approach'?'#ffd09a':'#94e6f1'):isIwo?(a.iwo_origin==='offspring'?'#c8ff91':'#f3b875'):isSa?'#ffc78a':isGsa?'#9adcfb':isDe?(a.de_accepted?'#a4ffcf':'#d5b2ff'):'#ffd18a');ctx.beginPath();ctx.arc(x,y,selected?5.2:(isGsa?3.1+6*Math.sqrt(Math.max(0,a.gsa_mass??0)):2.9+2*a.brightness),0,Math.PI*2);ctx.fill();
        if(selected){ctx.strokeStyle='#c1fff0';ctx.lineWidth=1.5;ctx.beginPath();ctx.arc(x,y,10,0,Math.PI*2);ctx.stroke()}
      }
      const [bestX,bestY]=frame.best_position;
      const x=px(bestX),y=py(bestY);
      ctx.strokeStyle='#82f4d2';ctx.lineWidth=2;ctx.beginPath();ctx.arc(x,y,11,0,Math.PI*2);ctx.stroke();
      ctx.beginPath();ctx.moveTo(x-16,y);ctx.lineTo(x-9,y);ctx.moveTo(x+9,y);ctx.lineTo(x+16,y);ctx.moveTo(x,y-16);ctx.lineTo(x,y-9);ctx.moveTo(x,y+9);ctx.lineTo(x,y+16);ctx.stroke();
    }else{
      ctx.textAlign='center';ctx.fillStyle='#b8d3d5';ctx.font='600 15px system-ui';
      ctx.fillText('Simülasyonu başlatarak ajan hareketlerini izle',w/2,h/2);ctx.textAlign='left';
    }
  },[bg,bounds,frame,run,size,selectedId,trails,showTargets]);
  const selected=frame?.agents.find(a=>a.id===selectedId);
  return <div className="landscape-area" ref={wrapRef}>
    <canvas ref={canvasRef} className="landscape-canvas" style={{height:size.height}}
      role="img" aria-label="Amaç fonksiyonu yüzeyinde ajanların konumu, izleri ve hareket bilgileri"
      onClick={e=>{
        if(!frame) return;
        const rect=e.currentTarget.getBoundingClientRect();
        const x=e.clientX-rect.left,y=e.clientY-rect.top;
        const pl=44,pt=24,pw=size.width-68,ph=size.height-60;
        const hovered=frame.agents.find(a=>Math.hypot(pl+(a.x-bounds[0])/(bounds[1]-bounds[0])*pw-x,pt+(bounds[1]-a.y)/(bounds[1]-bounds[0])*ph-y)<13);
        setSelectedId(hovered?.id ?? null);
      }}/>
    <div className="plot-top-chip"><span className="pulse-dot"/> 2B ARAMA UZAYI <span>·</span> {objective.toUpperCase()}</div>
    <div className="plot-legend"><span><i className="legend-firefly"/> Ajan</span><span><i className="legend-best"/> En iyi kayıt</span></div>
    {selected && <div className={`agent-popover ${run?.algorithm==='de'?'de-popover':''}`}><div className="popover-title">{run?.algorithm==='pso'?'PARÇACIK':run?.algorithm==='abc'?'BESİN KAYNAĞI':run?.algorithm==='cs'?'YUVA':run?.algorithm==='mfo'?'GÜVE':run?.algorithm==='gwo'?'KURT':run?.algorithm==='woa'?'BALİNA':run?.algorithm==='ba'?'YARASA':run?.algorithm==='ssa'?'SALP':run?.algorithm==='sma'?'CIVIK MANTAR':run?.algorithm==='iwo'?'YABANİ OT':run?.algorithm==='sa'?'MEVCUT ÇÖZÜM':run?.algorithm==='gsa'?'KÜTLE':run?.algorithm==='de'?'DE BİREYİ':'ATEŞBÖCEĞİ'} #{selected.id+1}<button onClick={()=>setSelectedId(null)} aria-label="Seçimi kaldır">×</button></div><div>Konum <strong>({numberFmt(selected.x,2)}, {numberFmt(selected.y,2)})</strong></div><div>Uygunluk <strong>{numberFmt(selected.fitness,5)}</strong></div>{run?.algorithm==='de'?<>
      <div>Eski hedef <strong>{selected.de_parent?selected.de_parent.map(v=>numberFmt(v,4)).join(' / '):'Başlangıç'}</strong></div>
      <div>Donörler (r₁/r₂/r₃) <strong>{selected.de_donors?selected.de_donors.map(i=>`#${i+1}`).join(' / '):'—'}</strong></div>
      <div>Fark mutasyonu (F) <strong>{numberFmt(run.parameters?.de_mutation_factor??.75,3)}</strong></div>
      <div>Ham mutant <strong>{selected.de_mutant_raw?selected.de_mutant_raw.map(v=>numberFmt(v,4)).join(' / '):'—'}</strong></div>
      <div>Kırpılmış mutant <strong>{selected.de_mutant?selected.de_mutant.map(v=>numberFmt(v,4)).join(' / '):'—'}</strong></div>
      <div>Çaprazlama maskesi (x/y) <strong>{selected.de_crossover_mask?selected.de_crossover_mask.map(b=>b?'V':'X').join(' / '):'—'}</strong></div>
      <div>jrand (zorunlu) <strong>{selected.de_j_rand==null?'—':selected.de_j_rand===0?'X ekseni':'Y ekseni'}</strong></div>
      <div>Deneme vektörü <strong>{selected.de_trial?selected.de_trial.map(v=>numberFmt(v,4)).join(' / '):'—'}</strong></div>
      <div>Deneme uygunluğu <strong>{selected.de_trial_fitness==null?'—':numberFmt(selected.de_trial_fitness,6)}</strong></div>
      <div>Seçim kararı <strong>{selected.de_accepted==null?'Başlangıç':selected.de_accepted?'Kabul':'Reddedildi'}</strong></div>
    </>:run?.algorithm==='gsa'?<>
      <div>Normalize kütle Mᵢ <strong>{numberFmt(selected.gsa_mass??0,6)}</strong></div>
      <div>Çekimde kullanılan kütle <strong>{selected.gsa_force_mass==null?'Başlangıç':numberFmt(selected.gsa_force_mass,6)}</strong></div>
      <div>G(t) / Kbest <strong>{numberFmt(frame!.gsa_gravity??0,7)} / {frame!.gsa_kbest}</strong></div>
      <div>Önceki konum <strong>{selected.gsa_previous?selected.gsa_previous.map(v=>numberFmt(v,3)).join(' / '):'—'}</strong></div>
      <div>En büyük tek çekim kaynağı <strong>{selected.target_id==null?'Yok':`#${selected.target_id+1}`}</strong></div>
      <div>Çekim kaynağının eski konumu <strong>{selected.gsa_attractor?selected.gsa_attractor.map(v=>numberFmt(v,3)).join(' / '):'—'}</strong></div>
      <div>Kuvvet (Fx / Fy) <strong>{selected.gsa_force?selected.gsa_force.map(v=>numberFmt(v,4)).join(' / '):'—'}</strong></div>
      <div>İvme (ax / ay) <strong>{selected.gsa_acceleration?selected.gsa_acceleration.map(v=>numberFmt(v,4)).join(' / '):'—'}</strong></div>
      <div>Hız (vx / vy) <strong>{numberFmt(selected.vx??0,4)} / {numberFmt(selected.vy??0,4)}</strong></div>
      <div>Hız katsayıları U <strong>{selected.gsa_velocity_draw?selected.gsa_velocity_draw.map(v=>numberFmt(v,4)).join(' / '):'—'}</strong></div>
    </>:run?.algorithm==='pso'?<>
      <div>Hız vektörü <strong>({numberFmt(selected.vx??0,3)}, {numberFmt(selected.vy??0,3)})</strong></div>
      <div>pBest <strong>({numberFmt(selected.pbest_x??0,2)}, {numberFmt(selected.pbest_y??0,2)})</strong></div>
      <div>pBest uygunluğu <strong>{numberFmt(selected.pbest_fitness??0,5)}</strong></div>
      <div>gBest <strong>({numberFmt(frame!.best_position[0],2)}, {numberFmt(frame!.best_position[1],2)})</strong></div>
    </>:run?.algorithm==='abc'?<><div>Son işlem <strong>{selected.role==='scout'?'Keşifçi':selected.role==='onlooker'?'Gözlemci':'İşçi'}</strong></div><div>Başarısız denemeler <strong>{selected.trials??0}</strong></div><div>Gözlemci seçilme olasılığı <strong>%{((selected.selection_probability??0)*100).toFixed(2)}</strong></div><div>Komşu referansı <strong>{selected.target_id==null?'Yok':`#${selected.target_id+1}`}</strong></div></>:run?.algorithm==='cs'?<><div>Son işlem <strong>{selected.move_kind==='levy'?'Kabul edilen Lévy uçuşu':selected.move_kind==='abandoned'?'Terk / yeniden oluşturma':'Korundu / reddedildi'}</strong></div><div>Son önerilen uçuş uzunluğu <strong>{numberFmt(selected.proposed_flight_length??0,4)}</strong></div><div>Global en iyi <strong>{numberFmt(frame!.best_so_far,6)}</strong></div></>:run?.algorithm==='mfo'?<><div>İzlenen alev <strong>{selected.flame_rank==null?'—':`#${selected.flame_rank+1}`}</strong></div><div>Alev konumu <strong>({numberFmt(selected.flame_x??0,3)}, {numberFmt(selected.flame_y??0,3)})</strong></div><div>Spiral t (x / y) <strong>{numberFmt(selected.spiral_t_x??0,3)} / {numberFmt(selected.spiral_t_y??0,3)}</strong></div><div>Aktif alev sayısı <strong>{frame!.flame_count??0}</strong></div></>:run?.algorithm==='gwo'?<><div>Hiyerarşi <strong>{selected.wolf_role==='alpha'?'Alfa (α)':selected.wolf_role==='beta'?'Beta (β)':selected.wolf_role==='delta'?'Delta (δ)':'Omega (ω)'}</strong></div><div>Kuşatma katsayısı a <strong>{numberFmt(frame!.gwo_a??0,3)}</strong></div><div>Harekette kullanılan liderler <strong>{(frame!.gwo_leader_ids??[]).map(id=>`#${id+1}`).join(' / ')}</strong></div><div>Alfa adayı X₁ <strong>{selected.gwo_x1?`(${numberFmt(selected.gwo_x1[0],2)}, ${numberFmt(selected.gwo_x1[1],2)})`:'Başlangıç'}</strong></div><div>Beta adayı X₂ <strong>{selected.gwo_x2?`(${numberFmt(selected.gwo_x2[0],2)}, ${numberFmt(selected.gwo_x2[1],2)})`:'Başlangıç'}</strong></div><div>Delta adayı X₃ <strong>{selected.gwo_x3?`(${numberFmt(selected.gwo_x3[0],2)}, ${numberFmt(selected.gwo_x3[1],2)})`:'Başlangıç'}</strong></div><div>En iyi arşiv <strong>{numberFmt(frame!.best_so_far,7)}</strong></div></>:run?.algorithm==='woa'?<><div>Son hareket <strong>{selected.woa_move_kind==='search'?'Rastgele balina keşfi':selected.woa_move_kind==='encircle'?'Avı kuşatma':selected.woa_move_kind==='spiral'?'Baloncuk-ağı spirali':'Başlangıç'}</strong></div><div>a katsayısı <strong>{numberFmt(frame!.woa_a??0,3)}</strong></div><div>Önceki konum <strong>{selected.woa_previous?`(${numberFmt(selected.woa_previous[0],3)}, ${numberFmt(selected.woa_previous[1],3)})`:'—'}</strong></div><div>Hedef konum <strong>{selected.woa_target?`(${numberFmt(selected.woa_target[0],3)}, ${numberFmt(selected.woa_target[1],3)})`:'—'}</strong></div><div>Rastgele akran <strong>{selected.woa_target_id!=null?`#${selected.woa_target_id+1}`:'—'}</strong></div><div>Seçim p <strong>{selected.woa_p==null?'—':numberFmt(selected.woa_p,4)}</strong></div><div>A vektörü <strong>{selected.woa_A?`(${numberFmt(selected.woa_A[0],3)}, ${numberFmt(selected.woa_A[1],3)})`:'Spiral'}</strong></div><div>C vektörü <strong>{selected.woa_C?`(${numberFmt(selected.woa_C[0],3)}, ${numberFmt(selected.woa_C[1],3)})`:'Spiral'}</strong></div><div>Spiral ℓ <strong>{selected.woa_l==null?'—':numberFmt(selected.woa_l,4)}</strong></div></>:run?.algorithm==='ba'?<><div>Hareket <strong>{selected.ba_move_kind==='local'?'Yerel arama':selected.ba_move_kind==='global'?'Frekans-hız adımı':'Başlangıç'}</strong></div><div>Durum <strong>{selected.ba_accepted==null?'Başlangıç':selected.ba_accepted?'Aday kabul edildi':'Aday reddedildi (NFE sayıldı)'}</strong></div><div>Frekans <strong>{numberFmt(selected.ba_frequency??0,4)}</strong></div><div>Hız (vx / vy) <strong>{numberFmt(selected.vx??0,3)} / {numberFmt(selected.vy??0,3)}</strong></div><div>Ses şiddeti A <strong>{numberFmt(selected.ba_loudness??0,4)}</strong></div><div>Darbe oranı r <strong>{numberFmt(selected.ba_pulse_rate??0,4)}</strong></div><div>Önceki konum <strong>{selected.ba_previous?`(${numberFmt(selected.ba_previous[0],3)}, ${numberFmt(selected.ba_previous[1],3)})`:'—'}</strong></div><div>Önerilen aday <strong>{selected.ba_candidate?`(${numberFmt(selected.ba_candidate[0],3)}, ${numberFmt(selected.ba_candidate[1],3)})`:'—'}</strong></div><div>Aday uygunluğu <strong>{selected.ba_candidate_fitness==null?'—':numberFmt(selected.ba_candidate_fitness,6)}</strong></div><div>Önceki en iyi referans <strong>{selected.ba_reference_best?`(${numberFmt(selected.ba_reference_best[0],3)}, ${numberFmt(selected.ba_reference_best[1],3)})`:'—'}</strong></div><div>Yerel ε (x / y) <strong>{selected.ba_local_epsilon?`${numberFmt(selected.ba_local_epsilon[0],3)} / ${numberFmt(selected.ba_local_epsilon[1],3)}`:'—'}</strong></div><div>Önceki ort. ses A <strong>{selected.ba_mean_loudness==null?'—':numberFmt(selected.ba_mean_loudness,4)}</strong></div><div>Darbe örneği U <strong>{selected.ba_pulse_draw==null?'—':numberFmt(selected.ba_pulse_draw,4)}</strong></div><div>Kabul örneği U <strong>{selected.ba_accept_draw==null?'—':numberFmt(selected.ba_accept_draw,4)}</strong></div></>:run?.algorithm==='sa'?<><div>Sıcaklık T <strong>{numberFmt(frame!.sa_temperature??0,6)}</strong></div><div>Karar <strong>{selected.sa_accepted==null?'Başlangıç':selected.sa_accepted?'Kabul':'Ret (aday değerlendirildi)'}</strong></div><div>Önceki konum <strong>{selected.sa_previous?selected.sa_previous.map(v=>numberFmt(v,4)).join(' / '):'—'}</strong></div><div>Aday konum <strong>{selected.sa_candidate?selected.sa_candidate.map(v=>numberFmt(v,4)).join(' / '):'—'}</strong></div><div>Aday uygunluğu <strong>{selected.sa_candidate_fitness==null?'—':numberFmt(selected.sa_candidate_fitness,6)}</strong></div><div>Δf <strong>{selected.sa_delta==null?'—':numberFmt(selected.sa_delta,6)}</strong></div><div>Kabul olasılığı <strong>{selected.sa_accept_probability==null?'—':`${(100*selected.sa_accept_probability).toFixed(4)}%`}</strong></div><div>Rastgele çekiliş U <strong>{selected.sa_accept_draw==null?'—':numberFmt(selected.sa_accept_draw,6)}</strong></div><div>Gaussian adım <strong>{selected.sa_step?selected.sa_step.map(v=>numberFmt(v,4)).join(' / '):'—'}</strong></div><div>Tarihsel en iyi <strong>{numberFmt(frame!.best_so_far,7)}</strong></div></>:run?.algorithm==='iwo'?<><div>Durum <strong>{selected.iwo_origin==='offspring'?'Yeni filiz (hayatta kaldı)':'Eski bitki / hayatta kaldı'}</strong></div><div>Üretilen tohum <strong>{selected.iwo_seeds_produced??0}</strong></div><div>Ebeveyn <strong>{selected.iwo_parent_id==null?'—':`#${selected.iwo_parent_id+1}`}</strong></div><div>Gerçek ebeveyn konumu <strong>{selected.iwo_parent_position?`(${numberFmt(selected.iwo_parent_position[0],4)}, ${numberFmt(selected.iwo_parent_position[1],4)})`:'—'}</strong></div><div>Ham saçılma adımı <strong>{selected.iwo_raw_step?`(${numberFmt(selected.iwo_raw_step[0],4)}, ${numberFmt(selected.iwo_raw_step[1],4)})`:'—'}</strong></div><div>Doğum jenerasyonu <strong>{selected.iwo_birth_generation??'Başlangıç / eski'}</strong></div><div>σ (yayılma) <strong>{numberFmt(frame!.iwo_sigma??0,5)}</strong></div><div>Hayatta kalan popülasyon <strong>{frame!.iwo_population_after??frame!.agents.length}</strong></div></>:run?.algorithm==='sma'?<>
      <div>Son hareket <strong>{selected.sma_move_kind==='restart'?'Yeniden başlangıç':selected.sma_move_kind==='approach'?'Besine yaklaşma':selected.sma_move_kind==='contract'?'Büzülme':'Başlangıç'}</strong></div>
      <div>Uyarlamalı W <strong>{numberFmt(selected.sma_weight??1,5)}</strong></div>
      <div>Yaklaşma olasılığı p <strong>{numberFmt(selected.sma_probability??0,5)}</strong></div>
      <div>Kontrol sınırları a / b <strong>{numberFmt(frame!.sma_a??0,4)} / {numberFmt(frame!.sma_b??0,4)}</strong></div>
      <div>Eski konum <strong>{selected.sma_previous?`(${numberFmt(selected.sma_previous[0],3)}, ${numberFmt(selected.sma_previous[1],3)})`:'—'}</strong></div>
      <div>Arşivdeki besin <strong>{selected.sma_best_reference?`(${numberFmt(selected.sma_best_reference[0],3)}, ${numberFmt(selected.sma_best_reference[1],3)})`:'—'}</strong></div>
      <div>Kaynak XA / XB <strong>{selected.sma_source_a==null?'—':`#${selected.sma_source_a+1} / #${(selected.sma_source_b??0)+1}`}</strong></div>
      <div>vb / vc <strong>{selected.sma_vb?`${numberFmt(selected.sma_vb[0],3)}, ${numberFmt(selected.sma_vb[1],3)} / ${numberFmt(selected.sma_vc?.[0]??0,3)}, ${numberFmt(selected.sma_vc?.[1]??0,3)}`:'—'}</strong></div>
      <div>Karar / yeniden başlatma çekilişi <strong>{numberFmt(selected.sma_branch_draw??0,4)} / {numberFmt(selected.sma_restart_draw??0,4)}</strong></div>
    </>:run?.algorithm==='ssa'?<><div>Zincir rolü <strong>{selected.ssa_role==='leader'?'Lider (ilk salp)':'Takipçi'}</strong></div><div>Kontrol katsayısı c₁ <strong>{numberFmt(frame!.ssa_c1??0,6)}</strong></div><div>Önceki konum <strong>{selected.ssa_previous?`(${numberFmt(selected.ssa_previous[0],4)}, ${numberFmt(selected.ssa_previous[1],4)})`:'Başlangıç'}</strong></div><div>{selected.ssa_role==='leader'?'Besin kaynağı F':'Güncel öncül konum'} <strong>{selected.ssa_target?`(${numberFmt(selected.ssa_target[0],4)}, ${numberFmt(selected.ssa_target[1],4)})`:'Başlangıç'}</strong></div><div>Zincirdeki öncül <strong>{selected.target_id==null?'—':`#${selected.target_id+1}`}</strong></div><div>c₂ (x/y) <strong>{selected.ssa_c2?selected.ssa_c2.map(x=>numberFmt(x,4)).join(' / '):'Takipçi'}</strong></div><div>c₃ (x/y) <strong>{selected.ssa_c3?selected.ssa_c3.map(x=>numberFmt(x,4)).join(' / '):'Takipçi'}</strong></div><div>Zincir uzunluğu <strong>{numberFmt(frame!.ssa_chain_length??0,4)}</strong></div></>:<><div>Parlaklık <strong>%{Math.round(selected.brightness*100)}</strong></div><div>Hedef <strong>{selected.target_id===null?'Yok':`#${selected.target_id+1}`}</strong></div></>}</div>}
  </div>;
}
