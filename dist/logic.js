(function(root){
 const Logic={
  revenue(rows){
   const sum=k=>rows.reduce((n,r)=>n+r[k],0),start=sum('previous_arr_cents'),end=sum('arr_cents');
   const change=m=>rows.filter(r=>r.movement===m).reduce((n,r)=>n+r.delta_arr_cents,0);
   const newBusiness=change('New business'),expansion=change('Expansion'),contraction=change('Contraction'),churn=change('Churn');
   return {start,end,newBusiness,expansion,contraction,churn,delta:end-start,
    nrr:start?rows.filter(r=>r.previous_arr_cents>0).reduce((n,r)=>n+r.arr_cents,0)/start:null,
    grr:start?rows.filter(r=>r.previous_arr_cents>0).reduce((n,r)=>n+Math.min(r.arr_cents,r.previous_arr_cents),0)/start:null,
    active:rows.filter(r=>r.arr_cents>0).length,mismatches:rows.filter(r=>r.variance_cents!==0).length,
    reconciles:start+newBusiness+expansion+contraction+churn===end};
  },
  transition(current,command){
   if(command==='approve'&&current==='Needs review')return {status:'Approved',result:'approved'};
   if(command==='record'&&current==='Approved')return {status:'Recorded locally',result:'recorded'};
   if(command==='record'&&current==='Recorded locally')return {status:current,result:'duplicate_skipped'};
   return {status:current,result:'invalid_transition'};
  }
 };
 if(typeof module!=='undefined'&&module.exports)module.exports=Logic;else root.DemoLogic=Logic;
})(typeof window!=='undefined'?window:globalThis);
