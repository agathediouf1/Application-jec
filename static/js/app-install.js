(function(){
  var m=document.getElementById("appm");if(!m)return;
  var btn=document.getElementById("app-install"),dp=null;
  if(window.matchMedia&&window.matchMedia("(display-mode: standalone)").matches){document.querySelectorAll("[data-app-open]").forEach(function(el){el.style.display="none";});}
  function open(){m.hidden=false;document.body.style.overflow="hidden";}
  function close(){m.hidden=true;document.body.style.overflow="";}
  document.querySelectorAll("[data-app-open]").forEach(function(b){b.onclick=function(e){e.preventDefault();var n=document.getElementById("mob-nav");if(n&&n.classList.contains("open")){var bg=document.getElementById("burger");if(bg)bg.click();}open();};});
  m.querySelector(".appm-x").onclick=close;m.onclick=function(e){if(e.target===m)close();};
  document.addEventListener("keydown",function(e){if(e.key==="Escape"&&!m.hidden)close();});
  window.addEventListener("beforeinstallprompt",function(e){e.preventDefault();dp=e;btn.hidden=false;});
  btn.onclick=function(){if(!dp)return;dp.prompt();dp.userChoice.finally(function(){dp=null;btn.hidden=true;});};
  window.addEventListener("appinstalled",close);
  if("serviceWorker" in navigator&&(location.protocol==="https:"||location.hostname==="localhost")){navigator.serviceWorker.register("/sw.js").catch(function(){});}
})();
