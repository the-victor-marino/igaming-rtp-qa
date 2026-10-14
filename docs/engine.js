(function(root){
const probabilities=[.3,.25,.2,.15,.1],payouts=[5,10,15,25,50];
function payout(reels){return reels[0]===reels[1]&&reels[1]===reels[2]?payouts[reels[0]]:0;}
function draw(random=Math.random,rigged=false){const p=rigged?[.24,.2,.16,.12,.28]:probabilities;let r=random();for(let i=0;i<p.length;i++){r-=p[i];if(r<0)return i;}return 4;}
function seeded(seed){return ()=>{seed|=0;seed=seed+0x6D2B79F5|0;let t=Math.imul(seed^seed>>>15,1|seed);t=t+Math.imul(t^t>>>7,61|t)^t;return ((t^t>>>14)>>>0)/4294967296;};}
function simulate(n=20000,rigged=false){const random=seeded(42),counts=[0,0,0,0,0],points=[];let paid=0;for(let i=1;i<=n;i++){const reels=Array.from({length:3},()=>draw(random,rigged));reels.forEach(x=>counts[x]++);paid+=payout(reels);if(i%100===0)points.push([i,paid/i*100]);}const chi=counts.reduce((s,o,i)=>s+(o-3*n*probabilities[i])**2/(3*n*probabilities[i]),0);const p=Math.exp(-chi/2)*(1+chi/2);return {n,counts,points,chi,p,rtp:paid/n*100};}
const defaults={payout:{reels:[4,4,4]},funds:{balance:5,bet:8},race:{balance:10,bet:10,requests:2},limit:{loss:18,cap:20,bet:5}};
function validate(s,d){
 if(!defaults[s])return 'Choose a known scenario.';
 if(s==='payout')return Array.isArray(d.reels)&&d.reels.length===3&&d.reels.every(v=>Number.isInteger(v)&&v>=0&&v<5)?'':'Select all three symbols.';
 for(const [k,v] of Object.entries(d))if(typeof v!=='number'||!Number.isFinite(v)||Math.abs(v)>1000000)return 'Enter finite numbers between -1,000,000 and 1,000,000.';
 const whole=v=>Number.isInteger(v)&&v>=0;
 if(s==='funds')return whole(d.balance)?'':'Starting balance must be a nonnegative whole number.';
 if(s==='race')return whole(d.balance)&&Number.isInteger(d.bet)&&d.bet>0&&Number.isInteger(d.requests)&&d.requests>=2&&d.requests<=10?'':'Use a nonnegative whole balance, a positive whole stake and 2–10 requests.';
 if(s==='limit')return whole(d.loss)&&whole(d.cap)&&Number.isInteger(d.bet)&&d.bet>0?'':'Use nonnegative whole loss and cap, and a positive whole stake.';
 return '';
}
function check(scenario,bug,inputs=defaults[scenario]){
 const d={...defaults[scenario],...inputs},error=validate(scenario,d);if(error)return {error,pass:false};
 let rows=[],trace=[],detail='';const row=(label,expected,actual)=>({label,expected,actual,pass:expected===actual});
 if(scenario==='payout'){
  const expected=d.reels.every(v=>v===d.reels[0])?[5,10,15,25,50][d.reels[0]]:0;
  const actual=bug?Math.max(0,payout(d.reels)-10):payout(d.reels);
  rows=[row('Prize (credits)',expected,actual)];trace=[d.reels.every(v=>v===d.reels[0])?'Three matching symbols: look up the prize.':'Mixed symbols: no winning line.',bug?'Fault enabled: subtract 10 from a winning prize, floored at 0.':'Return the configured prize.'];detail='Exact payout comparison at the model’s fixed 1-credit stake.';
 }else if(scenario==='funds'){
  const valid=Number.isInteger(d.bet)&&d.bet>0,expected=valid&&d.bet<=d.balance;
  const actual=bug?true:valid&&d.balance>=d.bet;
  rows=[row('Bet decision',expected?'Accepted':'Rejected',actual?'Accepted':'Rejected'),row('Final balance',d.balance-(expected?d.bet:0),d.balance-(actual?d.bet:0))];
  trace=[`Start with ${d.balance} credits; request ${d.bet}.`,bug?'Fault enabled: skip amount and affordability checks.':valid?'Positive integer stake: check available credits.':'Invalid stake: reject zero, negative or fractional credits.',actual?'Accept and deduct the requested amount.':'Reject without changing the wallet.'];detail='Checks both the bet decision and exact wallet balance.';
 }else if(scenario==='race'){
  const expected=Math.min(d.requests,Math.floor(d.balance/d.bet));let balance=d.balance,accepted=0;
  if(bug){const snapshots=Array(d.requests).fill(balance>=d.bet);for(const ok of snapshots)if(ok){balance-=d.bet;accepted++;}}
  else for(let i=0;i<d.requests;i++)if(balance>=d.bet){balance-=d.bet;accepted++;}
  rows=[row('Accepted requests',expected,accepted),row('Final balance',d.balance-expected*d.bet,balance)];
  trace=[`${d.requests} requests each try to spend ${d.bet} from ${d.balance}.`,bug?'Unsafe schedule: every request checks the initial balance before any deduction.':'Serialized schedule: finish each check and deduction before the next request.',`${accepted} accepted; ${d.requests-accepted} rejected.`];detail='A deterministic replay of a race condition; the Python test uses actual threads.';
 }else{
  const expected=d.bet<=d.cap-d.loss,actual=bug?d.loss<d.cap:d.loss+d.bet<=d.cap;
  rows=[row('Next bet',expected?'Allowed':'Blocked',actual?'Allowed':'Blocked'),row('Net loss if the bet loses',d.loss+(expected?d.bet:0),d.loss+(actual?d.bet:0))];
  trace=[`Current loss ${d.loss}; next stake ${d.bet}; cap ${d.cap}.`,bug?'Fault enabled: check only whether current loss is below the cap.':'Include the full next stake before deciding.',actual?'Allow this stake; evaluate a losing outcome.':'Block this stake; do not increase the loss.'];detail=d.loss>d.cap?'The supplied loss already exceeds the cap. Blocking prevents further loss; it cannot undo prior loss.':'Checks the next-stake boundary, including an exact match with the cap.';
 }
 const pass=rows.every(r=>r.pass);return {pass,rows,trace,detail,latent:bug&&pass};
}
function playAction(state,config,reels,kind='spin'){
 const {stake,cap,requests=2,bugs={}}=config;
 if(![state.balance,state.start,stake,cap].every(Number.isFinite)||Math.abs(stake)>1000000||!Number.isInteger(cap)||cap<0||cap>1000000)throw Error('Enter a finite stake and a nonnegative whole loss cap, up to 1,000,000.');
 if(kind==='batch'&&(!Number.isInteger(requests)||requests<2||requests>10))throw Error('Use 2–10 simultaneous requests.');
 if(kind==='spin'&&(!Array.isArray(reels)||reels.length!==3||reels.some(x=>!Number.isInteger(x)||x<0||x>4)))throw Error('Choose three valid symbols.');
 function execute(faults){let balance=state.balance,accepted=0,prize=0;const trace=[];
  function decision(b){if(!faults.funds&&(!Number.isInteger(stake)||stake<=0))return 'Invalid stake';if(!faults.funds&&b<stake)return 'Insufficient balance';const loss=state.start-b;if(faults.limit?loss>=cap:loss+stake>cap)return 'Loss cap';return 'Accepted';}
  if(kind==='spin'){const reason=decision(balance);if(reason==='Accepted'){accepted=1;balance-=stake;const base=payout(reels);prize=base*stake;if(faults.payout&&base>0)prize=Math.max(0,prize-10*stake);balance+=prize;}trace.push(`${reason}.`,accepted?`Deduct ${stake}; credit prize ${prize}.`:'No deduction or prize.');return {balance,accepted,prize,decision:reason,trace};}
  const initial=decision(balance);for(let i=0;i<requests;i++){const reason=faults.race?initial:decision(balance);if(reason==='Accepted'){balance-=stake;accepted++;}trace.push(`Request ${i+1}: ${reason}.`);}return {balance,accepted,prize:0,decision:`${accepted} accepted`,trace};
 }
 const expected=execute({}),actual=execute(bugs),row=(label,e,a)=>({label,expected:e,actual:a,pass:e===a});
 const rows=[row(kind==='spin'?'Bet decision':'Accepted requests',kind==='spin'?expected.decision:expected.accepted,kind==='spin'?actual.decision:actual.accepted)];
 if(kind==='spin')rows.push(row('Prize (credits)',expected.prize,actual.prize));
 rows.push(row('Final balance',expected.balance,actual.balance),row('Net loss',Math.max(0,state.start-expected.balance),Math.max(0,state.start-actual.balance)));
 return {rows,pass:rows.every(r=>r.pass),state:{start:state.start,balance:actual.balance},expected,actual,kind};
}

const api={probabilities,payouts,payout,draw,seeded,simulate,check,defaults,validate,playAction};if(typeof module!=='undefined')module.exports=api;else root.LabEngine=api;
})(typeof window==='undefined'?globalThis:window);
