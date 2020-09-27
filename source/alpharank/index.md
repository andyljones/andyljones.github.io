---
title: Simplifying alpharank
description: n/a
date: 2020/09/27
publish: False
---
<script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
<script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
<script>window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']]
  }
};</script>

I was reading through the alpharank paper and noticed that in the derivation of the transition matrix, there's this series:

$$
\rho_{\sigma, \tau} = \left(1 + \sum_{l=1}^{m-1} e^{-l\alpha(f_\tau - f_\sigma)} \right)^{-1}
$$

Now when $\alpha$ is very large, most of the terms in this series become negligible! 

If $f_\tau > f_\sigma$, then all but the first term becomes negligible, so 
$$\rho_{\sigma, \tau} \approx \left(1 + e^{-\alpha(f_\tau - f_\sigma)} \right)^{-1}$$

And if $f_\tau < f_\sigma$, then all but the last term becomes negligible, so 

$$\rho_{\sigma, \tau} \approx \left(1 + e^{-(m-1)\alpha(f_\tau - f_\sigma)} \right)^{-1}$$

And in fact $m$ is usually pretty large too, so you can go further and approximate this as $\rho_{\sigma, \tau} \approx 0$.

I think the interplay between the terms in this series is much of what drives the changes in $\pi$ as you increase $\alpha$. When $\pi$ settles out for large $\alpha$, it's because the first/last terms have come to dominate. 

I did a quick [sanity check](https://gist.github.com/andyljones/e4d655a2ee433010d9eecc35d328026b) of this simplification using the OpenSpiel alpharank implementation, and on the Kuhn poker test data the simplification comes out to within 1 part in 10k error. But that's one test case, so before I go and make a PR to OpenSpiel I wanted to check

* Can you think of another example dataset that this is going to have much bigger error on? In particular, a dataset where $\alpha$ is large enough that $\pi$ has 'settled out', but that this approximation is still bad. 
* Is this actually at all useful/interesting?