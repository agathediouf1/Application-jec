(function(){
  var logo=(document.currentScript&&document.currentScript.dataset.logo)||"";
  var hist=[];try{hist=JSON.parse(sessionStorage.getItem("jecChat")||"[]");}catch(e){}
  var csrf=(document.querySelector('meta[name="csrf-token"]')||{}).content||"";
  var chips=["Qu'est-ce que la JEC ?","Que signifie Voir – Réfléchir – Agir ?","Quelles sont les fédérations ?","Comment rejoindre la JEC ?"];
  var root=document.createElement("div");root.className="jc";
  root.innerHTML='<section class="jc-panel" role="dialog" aria-label="Assistant JEC" hidden><div class="jc-head"><img src="'+logo+'" alt="" width="36" height="36"><div><strong>Assistant JEC</strong><small>Je réponds uniquement aux questions sur la JEC</small></div><button class="jc-x" aria-label="Fermer"><i class="bi bi-x-lg"></i></button></div>'+
   '<div class="jc-msgs" aria-live="polite"></div><div class="jc-chips"></div>'+
   '<form class="jc-form"><input type="text" maxlength="500" placeholder="Posez votre question sur la JEC…" aria-label="Votre question" autocomplete="off"><button aria-label="Envoyer"><i class="bi bi-send-fill"></i></button></form></section>';
  document.body.appendChild(root);
  var panel=root.querySelector(".jc-panel"),box=root.querySelector(".jc-msgs"),form=root.querySelector("form"),inp=form.querySelector("input"),ch=root.querySelector(".jc-chips");
  var triggers=document.querySelectorAll("[data-assistant]");
  function fill(d,text){
    var re=/(\/(?:documentation|glossaire|federations|qui-sommes-nous|activites|actualites|galerie|contact)[a-z0-9\-\/]*)/g,last=0,m;
    while((m=re.exec(text))){d.appendChild(document.createTextNode(text.slice(last,m.index)));var a=document.createElement("a");a.href=m[1];a.textContent=m[1];a.style.cssText="color:#1E6FD9;font-weight:600";d.appendChild(a);last=re.lastIndex;}
    d.appendChild(document.createTextNode(text.slice(last)));
  }
  function add(role,text,cls){var d=document.createElement("div");d.className="jc-m jc-"+role+(cls?" "+cls:"");fill(d,text);box.appendChild(d);box.scrollTop=box.scrollHeight;return d;}
  function save(){try{sessionStorage.setItem("jecChat",JSON.stringify(hist.slice(-10)));}catch(e){}}
  add("assistant","Bonjour ! Je suis l'assistant de la JEC. Posez-moi vos questions sur le mouvement, ses fédérations, ses activités ou ses documents.");
  hist.forEach(function(m){add(m.role,m.content);});
  if(hist.length)ch.style.display="none";
  chips.forEach(function(q){var b=document.createElement("button");b.type="button";b.textContent=q;b.onclick=function(){send(q);};ch.appendChild(b);});
  function toggle(o){panel.hidden=!o;triggers.forEach(function(t){t.setAttribute("aria-expanded",o);});if(o)setTimeout(function(){inp.focus();box.scrollTop=box.scrollHeight;},50);}
  triggers.forEach(function(t){t.onclick=function(e){e.preventDefault();toggle(panel.hidden);var n=document.getElementById("mob-nav");if(n&&n.classList.contains("open")){var b=document.getElementById("burger");if(b)b.click();}};});
  root.querySelector(".jc-x").onclick=function(){toggle(false);};
  document.addEventListener("keydown",function(e){if(e.key==="Escape")toggle(false);});
  var busy=false;
  function send(q){
    q=(q||"").trim();if(!q||busy)return;busy=true;ch.style.display="none";inp.value="";
    hist.push({role:"user",content:q});add("user",q);var t=add("assistant","L'assistant réfléchit…","jc-typing");
    fetch("/assistant/",{method:"POST",headers:{"Content-Type":"application/json","X-CSRFToken":csrf},body:JSON.stringify({messages:hist.slice(-10)})})
      .then(function(r){return r.json().then(function(d){return {ok:r.ok,d:d};});})
      .then(function(x){t.remove();if(x.ok){hist.push({role:"assistant",content:x.d.reply});add("assistant",x.d.reply);}else{hist.pop();add("assistant",x.d.error||"Une erreur est survenue.");}save();})
      .catch(function(){t.remove();hist.pop();add("assistant","Connexion impossible pour le moment. Réessayez dans un instant.");})
      .then(function(){busy=false;});
  }
  form.onsubmit=function(e){e.preventDefault();send(inp.value);};
})();
