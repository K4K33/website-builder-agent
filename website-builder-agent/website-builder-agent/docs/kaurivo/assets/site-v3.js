
(function(){
"use strict";
var h=document.getElementById("topbar");
function scrollTop(){if(h)h.classList.toggle("scrolled",window.scrollY>16)}
window.addEventListener("scroll",scrollTop,{passive:true});scrollTop();
var toggle=document.querySelector(".mobile-toggle"), menu=document.querySelector(".nav-menu");
if(toggle&&menu){
function close(){menu.classList.remove("open");toggle.setAttribute("aria-expanded","false")}
toggle.addEventListener("click",function(){var open=menu.classList.toggle("open");toggle.setAttribute("aria-expanded",String(open))});
document.addEventListener("keydown",function(e){if(e.key==="Escape")close()});
menu.querySelectorAll("a").forEach(function(a){a.addEventListener("click",close)});
}
var reduced=window.matchMedia&&window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if("IntersectionObserver" in window&&!reduced){
var io=new IntersectionObserver(function(entries){entries.forEach(function(e){if(e.isIntersecting){e.target.classList.add("is-visible");io.unobserve(e.target)}})},{rootMargin:"0px 0px -20px 0px",threshold:.09});
document.querySelectorAll(".reveal").forEach(function(el){io.observe(el)});
}else{document.querySelectorAll(".reveal").forEach(function(el){el.classList.add("is-visible")})}
var scene=document.querySelector(".hero-scene"), frame=document.querySelector(".scene-frame");
if(scene&&frame&&!reduced&&window.matchMedia("(hover:hover) and (pointer:fine)").matches){
var raf=0;
scene.addEventListener("pointermove",function(e){
if(raf)return;
var x=e.clientX,y=e.clientY;
raf=requestAnimationFrame(function(){
var r=scene.getBoundingClientRect(),nx=(x-r.left)/r.width-.5,ny=(y-r.top)/r.height-.5;
frame.style.setProperty("--ry",String(-8+nx*10)+"deg");
frame.style.setProperty("--rx",String(5-ny*7)+"deg");
raf=0;
});
},{passive:true});
scene.addEventListener("pointerleave",function(){if(raf){cancelAnimationFrame(raf);raf=0}frame.style.removeProperty("--ry");frame.style.removeProperty("--rx")});
}
var tabs=[].slice.call(document.querySelectorAll("[data-stage-button]")),prototype=document.querySelector(".prototype-window");
if(tabs.length&&prototype){
var stages=["outline","design","ready"];
var captions=["01 / Structure and user journey","02 / Visual direction","03 / Responsive implementation"];
function select(i){
tabs.forEach(function(t,j){t.setAttribute("aria-selected",String(j===i));t.tabIndex=j===i?0:-1});
prototype.setAttribute("data-state",stages[i]);
var label=prototype.querySelector(".proto-stage-label"), cap=document.querySelector(".prototype-caption");
if(label)label.textContent=stages[i]==="outline"?"STRUCTURE FIRST":stages[i]==="design"?"DESIGN DIRECTION":"READY FOR THE NEXT STEP";
if(cap)cap.textContent=captions[i]+" · illustrative concept";
}
tabs.forEach(function(t,i){t.addEventListener("click",function(){select(i)});
t.addEventListener("keydown",function(e){if(e.key==="ArrowRight"||e.key==="ArrowDown"||e.key==="ArrowLeft"||e.key==="ArrowUp"){e.preventDefault();var d=(e.key==="ArrowLeft"||e.key==="ArrowUp")?-1:1;var n=(i+d+tabs.length)%tabs.length;select(n);tabs[n].focus()}})});
select(0);
}
var faqs=[].slice.call(document.querySelectorAll("#faq-list details"));
faqs.forEach(function(d){d.addEventListener("toggle",function(){if(d.open){faqs.forEach(function(other){if(other!==d)other.open=false})}})});
var form=document.getElementById("enquiry-form");
if(form){
form.addEventListener("submit",function(e){
e.preventDefault();if(!form.reportValidity())return;
var value=function(id){return document.getElementById(id).value.trim()};
var fields=[["Name",value("name")],["Email",value("email")],["Company",value("company")],["Current website",value("website")||"Not provided"],["Project",value("service")],["Message",value("message")]];
var body=fields.map(function(v){return v[0]+": "+v[1]}).join("\n\n");
var subject="Website project enquiry — "+value("company").replace(/[\r\n]/g," ").slice(0,80);
var url="mailto:hello.kaurivo@gmail.com?subject="+encodeURIComponent(subject)+"&body="+encodeURIComponent(body);
var status=document.getElementById("form-status");
if(status)status.textContent="A draft should open in your email app. Check it and press Send there. If nothing opens, email us directly.";
window.location.href=url;
});
}
var year=document.getElementById("year");if(year)year.textContent=String(new Date().getFullYear());
document.addEventListener("visibilitychange",function(){document.body.classList.toggle("pause-motion",document.hidden)});
})();
