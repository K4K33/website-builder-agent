
(function(){
"use strict";
// The fixed header does not respond to scroll: scrolling must remain native and instant.
var toggle=document.querySelector(".mobile-toggle"), menu=document.querySelector(".nav-menu");
if(toggle&&menu){
function close(){menu.classList.remove("open");toggle.setAttribute("aria-expanded","false")}
toggle.addEventListener("click",function(){var open=menu.classList.toggle("open");toggle.setAttribute("aria-expanded",String(open))});
document.addEventListener("keydown",function(e){if(e.key==="Escape")close()});
menu.querySelectorAll("a").forEach(function(a){a.addEventListener("click",close)});
}
// All content is visible immediately; no scroll-triggered reveal gating.
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
// Native POST form uses FormSubmit; no fake success state or mailto intercept.
var year=document.getElementById("year");if(year)year.textContent=String(new Date().getFullYear());
})();
