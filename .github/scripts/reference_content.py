"""Add the reference reading shell without replacing existing article content."""
import re
from pathlib import PurePosixPath

def wrap_html(html: str, relative: str) -> str:
    if relative in {'index.html','research-lab.html'} or 'data-reference-content=' in html: return html
    prefix='../'*len(PurePosixPath(relative).parts[:-1]);assets=prefix+'assets/reference-site/'
    html=re.sub(r'(<body\b[^>]*)(>)',r'\1 data-reference-content="true"\2',html,count=1)
    additions=f'<link data-reference-shell="style" rel="stylesheet" href="{assets}content.css" media="screen">'
    if 'name="theme-color"' not in html: additions+='<meta data-reference-shell="theme" name="theme-color" content="#080b0b">'
    html=html.replace('</head>',additions+'</head>',1)
    if relative=='docs/index.html':
        media=f'<figure class="reference-media"><a href="{prefix}#/platform/charts"><img src="{assets}original-charts.png" width="1220" height="886" alt="Charts workspace with labelled synthetic development data"></a><figcaption>Charts · retained development capture · synthetic test data</figcaption></figure>'
    elif relative=='learn/index.html':
        media=f'<figure class="reference-media"><a class="reference-photo" href="{prefix}#/learn"><img src="{assets}laptop-scene.webp" width="1024" height="314" alt="Illustrative research workstation"><img src="{assets}laptop-screen.webp" width="1024" height="314" alt=""></a><figcaption>Models · synthetic development data in an illustrative setting</figcaption></figure>'
    else: media=''
    if media:
        html,n=re.subn(r'(<div role="group" class="landing-hero-visual[^>]*>)',lambda m:m[1]+'<!-- reference-media:start -->'+media+'<!-- reference-media:end -->',html,count=1)
        if n!=1:raise ValueError('Expected existing landing visual: '+relative)
    if relative=='strategy-claim-audit-checklist.html':
        nav='<nav class="site-nav" data-reference-added-nav aria-label="Primary"><div class="nav-inner"><a class="brand" href="./"><span class="brand-mark" aria-hidden="true"></span>TraderCockpit</a><div class="nav-links"><a href="docs/">Docs</a><a href="learn/">Learn</a><a href="methods/">Methods</a><a href="pricing/">Pricing</a><a href="support/">Support</a></div></div></nav>'
        html=html.replace('<main ', '<!-- reference-navigation:start -->'+nav+'<!-- reference-navigation:end --><main ',1)
        html=html.replace('</head>','<!-- reference-print:start --><style>@media print{[data-reference-added-nav]{display:none!important}}</style><!-- reference-print:end --></head>',1)
        html=html.replace('</body>','<!-- reference-search:start --><script src="assets/site-search.js" defer></script><!-- reference-search:end --></body>',1)
    return html

def unwrap_html(html: str) -> str:
    html=html.replace(' data-reference-content="true"','')
    for name in ['navigation','print','search']:
        html=re.sub(r'<!-- reference-'+name+r':start -->[\s\S]*?<!-- reference-'+name+r':end -->','',html)
    html=re.sub(r'<(?:link|meta) data-reference-shell="[^"]*"[^>]*>','',html)
    return re.sub(r'<!-- reference-media:start -->[\s\S]*?<!-- reference-media:end -->','',html)
