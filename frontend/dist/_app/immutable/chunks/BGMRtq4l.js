import{s as P}from"./BbpPz6ub.js";import{p as o}from"./CNm8LbRa.js";import{C as Y}from"./DOzRjYaw.js";import{R as z,S as F,T as R,j as S,l as q,k as U,U as Z,h as m,i as j,m as A,p as D,V as y,W as E,d as H,M as L,N as M,t as O,b as V,X as _,Y as w,Z as x,a as b,c as h,r as g,s as $,e as k}from"./DWKF18Ce.js";import"./CFpbhM_1.js";import{T as W}from"./TjOl-k4B.js";function X(a,t,u){m&&j();var d=a,r=Z,l,c=z()?F:R;S(()=>{c(r,r=t())&&(l&&q(l),l=U(()=>u(d)))}),m&&(d=A)}const B=()=>{const a=P;return{page:{subscribe:a.page.subscribe},navigating:{subscribe:a.navigating.subscribe},updated:a.updated}},te={subscribe(a){return B().page.subscribe(a)}};var G=L('<h5 class="me-1 text-xl leading-none font-bold text-gray-900 dark:text-white"> </h5> <p> </p> <div class="overflow-y-auto p-6"><!></div>',1);function le(a,t){D(t,!1);let u=o(t,"title",8),d=o(t,"subtitle",8),r=o(t,"column",8),l=o(t,"value",8),c=w(),v=w();y(()=>(x(r()),x(l())),()=>{_(c,{headings:r(),data:l()})}),y(()=>b(c),()=>{_(v,{data:b(c),perPage:5,perPageSelect:[5,10,15,20],sortable:!0,tableRender:(e,s,n)=>{const i=s.childNodes[0];i.childNodes[0].childNodes[0].attributes.class="datatable-sorter sm:sticky bg-gray-50 left-0 z-20"},rowRender:(e,s,n)=>{s.attributes.class="whitespace-nowrap lg:whitespace-pre-line",s.childNodes[0].attributes.class="sm:sticky bg-white left-0 z-10",s.childNodes[1].attributes.class="whitespace-nowrap",s.childNodes[2].attributes.class="whitespace-nowrap",s.childNodes[3].attributes.class="whitespace-nowrap"},columns:[{select:0,type:"string"},{select:1,type:"string"},{select:2,type:"string"},{select:3,type:"string"},{select:4,type:"number",render:e=>e.toFixed(2)},{select:5,type:"number",render:e=>e.toFixed(2)},{select:6,type:"number",render:e=>e.toFixed(2)},{select:7,key:"amount",type:"number"}],template:(e,s)=>`<div class='${e.classes.top}'>
        <div class='${e.classes.dropdown}'>
            <label>
                <select class='${e.classes.selector}'></select> ${e.labels.perPage}
            </label>
        </div>
        <div class='${e.classes.search}'>
            <input class='${e.classes.input}' placeholder='조건 검색' type='search' data-and="true" title='${e.labels.searchTitle}'${s.id?` aria-controls="${s.id}"`:""}>
        </div>
        </div>
        <div class='${e.classes.container}'${e.scrollY.length?` style='height: ${e.scrollY}; overflow-Y: auto;'`:""}></div>
        <div class='${e.classes.bottom}'>
        <div class='${e.classes.info}'></div>
        <nav class='${e.classes.pagination}'></nav>
    </div>`})}),E(),Y(a,{class:"p-4 md:p-6",size:"xl",children:(e,s)=>{var n=G(),i=M(n),N=h(i,!0);g(i);var p=$(i,2),T=h(p,!0);g(p);var f=$(p,2),C=h(f);X(C,l,I=>{W(I,{get dataTableOptions(){return b(v)}})}),g(f),O(()=>{k(N,u()),k(T,d())}),V(e,n)},$$slots:{default:!0}}),H()}export{le as C,X as k,te as p};
