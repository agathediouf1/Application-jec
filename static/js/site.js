(function(){
  var w=document.getElementById("welcome");
  if(w){
    if(sessionStorage.getItem("jecW")){w.remove();}
    else{sessionStorage.setItem("jecW","1");
      for(var i=0;i<30;i++){var h=document.createElement("span");h.className="heart "+(i%2?"b":"w");h.innerHTML='<i class="bi bi-heart-fill"></i>';
        h.style.cssText="left:"+Math.random()*100+"%;font-size:"+(18+Math.random()*34)+"px;animation-duration:"+(5+Math.random()*6)+"s;animation-delay:"+Math.random()*4+"s";w.appendChild(h);}
      var close=function(){w.classList.add("out");setTimeout(function(){w.remove();},700);};
      document.getElementById("w-ok").onclick=close;setTimeout(close,9000);}
  }
  var sel=".card,.team-card,.doc-card,.actu-card,.os-card,.section-chip,.page-header,.blue-block,.gal-item,.stat,.fed-panel-wrap,.id-grid";
  var els=document.querySelectorAll(sel),io=("IntersectionObserver" in window)?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");io.unobserve(e.target);}});},{threshold:.1}):null;
  els.forEach(function(el,i){el.classList.add("reveal");el.style.transitionDelay=(i%6)*70+"ms";if(io)io.observe(el);else el.classList.add("in");});
  var b=document.getElementById("burger"),n=document.getElementById("mob-nav");
  if(b){b.onclick=function(){var o=n.classList.toggle("open");b.classList.toggle("open",o);b.setAttribute("aria-expanded",o);document.body.style.overflow=o?"hidden":"";};
    n.onclick=function(e){if(e.target===n)b.click();};}
  document.querySelectorAll("[data-full]").forEach(function(f){f.onclick=function(){var l=document.createElement("div");l.className="lightbox";l.innerHTML='<img src="'+f.dataset.full+'" alt="">';l.onclick=function(){l.remove();};document.body.appendChild(l);};});
  var sl=document.getElementById("slider");
  if(sl){
    var sls=sl.querySelectorAll(".slide"),dts=sl.querySelectorAll(".sl-dots button"),cur=0,tm=null;
    var go=function(n){sls[cur].classList.remove("on");if(dts[cur])dts[cur].classList.remove("on");cur=(n+sls.length)%sls.length;sls[cur].classList.add("on");if(dts[cur])dts[cur].classList.add("on");};
    var stop=function(){clearInterval(tm);};
    var start=function(){stop();if(sls.length>1)tm=setInterval(function(){go(cur+1);},5000);};
    if(dts[0])dts[0].classList.add("on");
    var pv=sl.querySelector(".prev"),nx=sl.querySelector(".next");
    if(pv)pv.onclick=function(){go(cur-1);start();};if(nx)nx.onclick=function(){go(cur+1);start();};
    dts.forEach(function(d,i){d.onclick=function(){go(i);start();};});
    sl.onmouseenter=stop;sl.onmouseleave=start;
    var x0=null;sl.addEventListener("touchstart",function(e){x0=e.touches[0].clientX;},{passive:true});
    sl.addEventListener("touchend",function(e){if(x0===null)return;var dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>40){go(cur+(dx<0?1:-1));start();}x0=null;});
    start();
  }
  var hb=document.querySelectorAll(".hero-slide");
  if(hb.length>1){var hi=0,cap=document.getElementById("hero-cap");
    setInterval(function(){hb[hi].classList.remove("on");hi=(hi+1)%hb.length;hb[hi].classList.add("on");if(cap)cap.textContent=hb[hi].dataset.title||"";},6000);}
})();
