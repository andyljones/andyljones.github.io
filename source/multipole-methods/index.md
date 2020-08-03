---
title: The Recursive Approximation Algorithm, Animated
description: How n-body problems are solved in linear time, without any maths.
date: 2020/04/30
image: demo.jpg
category: Technical
---
# The Recursive Approximation Algorithm, Animated

<script type="module">
import {Runtime, Inspector} from "https://cdn.jsdelivr.net/npm/@observablehq/runtime/dist/runtime.js";
import notebook from "https://api.observablehq.com/d/dd1d583b63fccafd.js?v=3";

new Runtime().module(notebook, name => {
    var selection = document.getElementById(name);
    if (selection) {
        return new Inspector(selection);
    }
});
</script>

<video autoplay loop muted
    poster="/source/multipole-methods/demo.jpg"
    style="display:block; margin:auto; max-height:640px; width:100%">
      <source src="/source/multipole-methods/demo.mp4" type="video/mp4"/>
</video>

**This is not an epidemiological model**. It's a [tech demo for part of an epidemiological model](https://andyljones.com/pybbfmm/). What you're looking at is ten million simulated people in the United Kingdom. Each person has a small chance of infecting each other person in the country, and that chance drops with distance.

With ten million people, you'd think that each frame of the above animation would involve calculating a hundred trillion (ten million squared) interactions. Even for modern silicon, that's a lot! But there is a lesser-known algorithm from physics that can do it in a few seconds per frame.

That algorithm is the _fast multipole method_, but the 'multipole' bit scares lots of people off from an elegant, widely applicable idea. For that idea's sake I'm going to refer to it as the *recursive approximation algorithm*, and I'm going to explain it without using any algebra at all.

>  **Technical Summary**
> Fast multipole methods turn quadratic-time interaction problems into linear-time problems, and a recent version called the black-box multipole method can do it for any interaction you choose. The key idea is _a hierarchy of approximations_, and that's what most of this post is aimed towards explaining.

## Setup
Here's a _source_ and its _field_:

<div id='source_field' class='animation'></div>

Maybe the source is a planet and the field is its gravity. Maybe the source is a particle and the field is the electric field. Maybe the source is an infected person and the field is the transmission risk.

What the field represents isn't so important for our purposes, because whatever it represents the way to calculate it is the same. To calculate the field, we look at each of a 100 equally-spaced points in turn and calculate the strength of the source's field at each one:

<div id='source_points' class='animation'></div>

There are 100 points, so that took 100 calculations. 

If there's more than one source, then their fields add together. To calculate the combined field at a point, the field emitted by each source needs to be taken into account. With 100 sources and 100 points, there are 100 × 100 = 10,000 calculations to do:

<div id='sources_points' class='animation'></div>

## Groups
That's pretty wasteful though. If we've got a bunch of sources close to eachother like we do below, then they all make about the same contribution to the point. We could save a lot of work by using an approximation: move all the sources to the same spot, do _one_ calculation from that spot, and then multiply the calculated field strength by the number of sources in the group:

<div id='source_group_far' class='animation'></div>

If we look closely, we can see that the point doesn't _quite_ lie on the field line. This is because we can only get away with this kind of approximation when the point is far from the sources. When the point is far from the sources, the sources can be shifted left or right a bit without it mattering much. If the point is close to the sources though, then the exact location of each source is important, and the approximation doesn't work so well:

<div id='source_group_near' class='animation'></div>

This time the approximation misses by a lot!

Fortunately though most points are far way from most sources, so _most_ of the time the approximation works fine. 

So here's a plan:

  * Divide the sources into groups.
  * For all the points _far_ from a group do one calculation for the whole group.
  * For all the points _near_ to a group do one calculation for each source in the group.

What's 'near' and 'far' mean here? Well, the worst case scenario is if the approximation is used on a point that's _right next to the sources being approximated_. As a simple way to avoid this worst-case, we'll say a point is 'far' from a group if it doesn't sit under that group or the group's neighbours. That guarantees the point won't be right next door to the approximation. 

This plan is pretty simple, but it's already much faster:

<div id='source_small_groups' class='animation'></div>

Rather than the original 10,000 calculations we're now doing 

  * 1,000 calculations with nearby sources, and
  * 2,500 calculations with far groups

for 3,500 calculations total - a 65% improvement! That's no small thing - but can we do better?

## Groups of Groups
Well, the group sizes above were totally arbitrary. There's no reason they can't be twice as big:

<div id='source_big_groups' class='animation'></div>

Now we're doing 

  * 2,000 calculations with nearby sources, and
  * 1,200 calculations with far groups

for 3,200 calculations in total. That's a bit better overall, but what about if we could get _both_ the small number of near calculations from the previous example and the small number of far calculations from this one?

How about using both the the big scale and small scale at the same time? Now the plan looks like:

  * Divide the sources into both big groups and small groups.
  * Use the big group approximation on any points far away _in the big group scale_.
  * Use the small group approximation on any leftover points far away _in the small group scale_.
  * Use direct calculation for the leftover points that are near in the small scale.

We're basically changing the idea of 'near' and 'far' depending on whether we're looking at big groups or small groups. The logic is that the approximate calculation with the big group might move the sources a long way, and so the approximation is only going to be accurate at a big distance. Smaller groups move the sources less, and so the approximation is going to be accurate at a smaller distance.

Trying it out:

<div id='source_group_both' class='animation'></div>

does get us down to 2,500 calculations, but there's no reason we can't repeat this bigger-groups trick a few more times:

<div id='source_group_hierarchy' class='animation'></div>

Now it's only 2,000 calculations!

**This is the key idea in the recursive approximation algorithm**: rather than using one approximation that can only be used at one scale, we should build a _hierarchy_ of approximations. Small approximations can be used to replace the short-range calculations that require high accuracy, while big approximations can be used to replace the more numerous low-accuracy long-range calculations.

For example: at the top level of the previous animation, the approximation might involve moving a source fully one-eighth of the way across the screen! We get away with it because that approximation is only ever used with points more than quarter a screen away from the source. The lowest level of approximations meanwhile only ever get used to replace a small number of calculations, but they're accurate from 1/16th of a screen on out.

80% fewer calculations is great, but can we do better?

## Even More Groups
So the grouping idea relies on the fact that the greater the distance between a source and point, the less accurate we have to be about exactly where the _source_ is. But we can rephrase that and also say: the greater the distance between a source and point, the less accurate we have to be about exactly where the _point_ is!

That is, we can group the points just like we did the sources!

<div id='source_point_group' class='animation'></div>

We can see where this is going. Returning to one layer of groups, grouping both sources and points looks like this:

<div id='groups' class='animation'></div>

And just like before, we can stack groups of different sizes to make things even faster:

<div id='hierarchy' class='animation'></div>

This is the _recursive approximation algorithm_ at its core: recursively approximate the sources, recursively approximate the points, and get 10,000 calculations down to 1,000.

That's the end of the expository part of this post. What follows is decidedly more technical, and discusses the details of the method in the real world.

## Real-world problems
The problem explained above is simplified a _lot_ from the kind you'd see in the wild. 

The first - obvious - simplification is that the problems given here are all 1D, when the typical problem of interest is 2D or 3D. The same ideas work just as well in higher dimensions however, and it's possible to design code that handles problems of any dimension.
    
Next, the sources here all make the same strength contribution. In the wild, each source usually has a differing mass or charge or infectiousness. This is easy enough to handle: rather than counting the sources when you gather the sources to the middle of a group, you sum them instead. 

Finally, the sources and points in the problem above are evenly distributed. Each group at the bottom has roughly the same number of sources and points in. In the real world this isn't usually the case. The fix is to replace the 'full' binary tree shown above with an 'adaptive' binary tree that splits further in regions of higher density. This introduces a fairly substantial amount of complexity.

In its full generality, the recursive approximation algorithm will accelerate any problem that involves measuring the summed influence of many sources at many points. The only restrictions are that each source's field needs to be the same 'shape', differing only in scale, and the field shape needs to be 'nice' in some reasonable ways.

## Real-world approximations
In the algorithm described above, the approximation used is the simplest possible: it's a constant across the group, and the constant is the field strength at the center of the group. This has the advantage of being easy to explain, and frankly for many purposes it'll do just fine. Some toy experiments using a constant approximation gave me an MSE of about .1%. But if you want higher accuracy than that, either you need to widen the neighbourhood you consider 'near' so more source-point pairs get their contributions calculated exactly, or you need a better approximation. 

When the algorithm was first developed for physics simulations in the 1980s, the approximation of choice was a [Laurent series](https://en.wikipedia.org/wiki/Laurent_series). It makes for a really good approximation, but requires a fair bit of hand-rolled maths catered to exactly the field you're looking at. This is where the name 'multipole method' comes from, as Laurent series are defined around 'poles' where the approximation becomes infinite. Each group has it's own 'pole', and hence, multipole!

The name is a bit of a shame, since the key idea has nothing to do with Laurent series or poles. I suspect if this algorithm had been called the 'recursive approximation method', it'd be a lot more widely known.

In the more recent 'black-box' version from the late 2000s, a [Chebyshev approximation](https://en.wikipedia.org/wiki/Chebyshev_polynomials) is used instead. The advantage of the Chebyshev approximation is that it requries no domain-specific tuning at all: you can pass an arbitrary field to the code and it'll figure things out by evaluating it at a handful of points. The downside to the Chebyshev approximation is that it requires more variables and more computation for a given level of accuracy than the Laurent approach, though there are ways to fix this.

In both cases, the number of coefficients used by the approximation can be adjusted. More coefficients means exponentially better accuracy, but a polynomially slower computation.

## Real-world subtleties
Using the recursive approximation algorithm usually only speeds things up for large problems. Depending on how well-optimized your code is, the 'crossover point' where the algorithm is actually faster than the direct method can be anywhere between a few thousand points and tens of millions. Since the recursive approximation algorithm is asymptotically faster it _will_ eventually win out, but in the real world you might discover that you run out of memory first.

Eagle-eyed readers will have noticed that while I've claimed the recursive approximation algorithm is linear-time, the method involves constructing a tree of groups. Constructing a tree takes more than linear time, so what gives? Well, typical problems aren't usually stand-alone, but are solved again and again with very similar configurations of sources and points. The epidemiology demo from the top of the page is a case in point: the 'people' in the demo are in the same place at each step, so the tree of groups is the same at each step. With the tree fixed in place, _then_ the method is linear. 

In problems where the sources or points move from step-to-step though, the tree needs to be updated. Fortunately in most of the problems where sources or points move, they don't move _much_ each time, and you can dynamically re-compute just the bit of the tree that's relevant rather than starting over from scratch.

Something else that's ignored in the animations above is that in practice, repeatedly updating each point would slow things down to worse than linear time. The solution is to instead make two passes through the whole tree. The first pass is from the bottom up, using the source density of each child group to infer the source density of the parent. Then the second pass is from the top down, calculating the field strength at the center of each group using the field strength at the parent and the source density at the group's siblings. This way the field strength at each group and point is only updated once.

Finally, there is the issue that these are all approximation methods. Approximation methods give approximate answers, and without the _true_ solution to hand you can't tell how accurate the approximation is. Instead, we have to fall back on an analytical bound on the error. There are explicit bounds available for the classical Laurent-series based version, but frustratingly the paper for the black-box version only offers empirical evidence that the error improves as the number of coefficients increases. I have some scrawled workings showing that like the classical version, the error improves exponentially with the number of coefficients, but my theory is rusty enough that I'm not keen to publish them.

## Implementing it Yourself
As with all intricate numerical algorithms, the most important thing is to test it against a slower, simpler version. This is particularly true of the recursive approximation algorithm, where the direct approach can be written in one line of Python. It's especially useful to design your test problems so they isolate parts of the maths, like

  * check it matches the direct method when you've one source and one point and they're in the _same_ group
  * check it matches the direct method when you've one source and one point and they're in _neighbouring_ groups
  * check it matches the direct method when you've one source and one point and they're _not_ in neighbouring groups
  * etc etc etc

One of the nice things about the recursive approximation algorithm in particular is that the intermediate values computed by the method have physical, interpretable values. That's a strong contrast to many other numerical schemes, where the intermediate values are really hard to sanity-check.

The _other_ nice thing about it comes back to the tree-reuse mentioned above. Most of the complexity comes from building the tree and building lists of which groups interact with which. That can all be implemented and verified independently of the actual numeric code, meaning you can write it in two modules of tolerable complexity rather than one module of horrifying complexity.

The basics of unit testing aside, I would strongly advise you to implement a version using _static trees_ and a _constant approximation_ first. Swapping either of those out - to adaptive trees or a better approximation - will likely introduce a lot of new flaws that hide any older flaws in your core implementation.

## References
* The genesis of all these words was [my own GPU-accelerated, general-dimensional, dynamic-tree black-box fast multipole method](https://github.com/andyljones/pybbfmm) implementation. Fair warning, the code could use some comments.

* This key idea of 'recursive approximation' turns up in a few places. I've previously run into it
  * with [pyramids](https://en.wikipedia.org/wiki/Pyramid_%28image_processing%29) while doing medical image analysis
  * with [multigrid methods](https://en.wikipedia.org/wiki/Multigrid_method) when writing a simple weather model 
  * with [wavelets](https://en.wikipedia.org/wiki/Wavelet_transform) in signals analysis

* Most of the educational resources on fast multipole methods take a much more mathematical bent than I have here. They're also focused on the classic, Laurent-series-based version. Of those resources, my favourites are 
    * [Carrier, Greengard & Rokhlin's original paper](https://pdfs.semanticscholar.org/97f0/d2a31d818ede922c9a59dc17f710642332ca.pdf), which is both wonderfully detailed _and_ one of the few resources to describe dynamic trees.
    * [Demmel's lecture](https://people.eecs.berkeley.edu/~demmel/cs267_Spr16/Lectures/lecture25_NBody_jwd16_4pp.pdf) and [the code from one of his students](https://github.com/lbluque/fmm/blob/master/fmm.py).
    * [The Low-Rank Matrix Perspective](https://www.ics.uci.edu/~ihler/papers/ihler_area.pdf), which also points to links to the fast Gauss transform.

* While all the attention is on the classical version, the black-box fast multipole method is a great deal more flexible and conceptually simpler to boot.
  * [William & Fong's original paper](https://mc.stanford.edu/cgi-bin/images/f/fa/Darve_bbfmm_2009.pdf) is the best place to start. 
  * They also have [reference MATLAB code](https://github.com/sivaramambikasaran/BBFMM2D) and [a port of it to Python](https://github.com/DrFahdSiddiqui/bbFMM2D-Python).

* The stylistic inspiration for this post was [Bartosz Ciechanowski's excellent post on gears](https://ciechanow.ski/gears/) and [Jez Swanson's equally excellent post on the fourier transform](http://www.jezzamon.com/fourier/index.html).

* All of this was assembled in the fantastic [ObservableHQ](https://observablehq.com). This was my first experience with the platform, and while animation is _still_ excruciatingly slow to put together, ObservableHQ made it much less so than I feared it would be. [You can find the code underlying this post here](https://observablehq.com/d/dd1d583b63fccafd).
