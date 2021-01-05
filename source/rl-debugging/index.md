---
title: Debugging Reinforcement Learning Systems
description: How to debug your reinforcement learning implementations, without the agonizing pain 
date: 2021/01/01
category: Technical
publish: False
---
# Debugging RL While Preserving Your Sanity

<span style="color: red">This is still a draft. While you may find it useful, please do not share it until it's complete.</span>

Debugging reinforcement learning systems is incredibly painful. Debugging RL systems combines the fun of debugging distributed systems with the fun of debugging numerical optimizers. If this is your first time, you might plausibly have a few hundred lines of code that you *think* are correct in an hour, and a system that's *actually* correct two months later. [Here's the head of Tesla AI having exactly that experience](https://news.ycombinator.com/item?id=13519044).

This article is a collection of debugging advice that has served me well over the past few years. It both expands on the best advice previously available (principally [Matthew Rahtz's](http://amid.fish/reproducing-deep-rl), [Joshua Achiam's](https://spinningup.openai.com/en/latest/spinningup/spinningup.html#learn-by-doing), and [John Schulman's](https://github.com/williamFalcon/DeepRLHacks)), and supplements it with my own knowledge.

There are two sections: one on [theory](#theory), and one on [practice](#practice). Things flow a little better if you read the theory before the practice, but you can skip on ahead if you wish.

# Theory

## Why is debugging RL so hard?
A combination of issues. These issues show up in debugging any kind of system, but in RL they're both more common and they'll show up starting with the first system you ever write.

### Feedback is poor

**Errors aren't local**: The vast majority of the bugs you're likely to make are of the 'doing the wrong calculation' sort. Because information in an RL system flows in a loop - actor to learner and then back to actor - a numerical error in one spot gets smeared throughout the system in a few seconds, poisoning everything. This means that most numerical errors manifest as *all* your metrics going weird at the same time; your loss exploding, your KL div collapsing, your rewards oscillating. From the outside, you can tell something is wrong but you've no idea *what* is wrong or where to start looking. 

To my mind this is the single biggest issue with debugging RL systems, and much of the advice below is about how to better-localise errors. 

**Performance is noisy**: The ultimate arbiter of an RL system - how good it is at collecting reward - is only weakly related to how good of an implementation you've written. You could write a bug-free implementation the first time and other factors (like hyperparameters, architecture or your environment) could saboutage performance. In the worst case, your evaluation run could just get an unlucky seed. Conversely, you could write a bug-laden implementation and it might seem to work! After all, bugs are just one more source of noise and your neural net is going to [try its damnedest](https://twitter.com/gwern/status/1014978860369182722) to pull the signal out of that mess you're feeding it.

The real kicker though is that because run-to-run variability is so high, it's very easy to fix - or introduce - a bug and then see no change in performance at all. 

### Simplifying is hard
**There're few narrow interfaces**: Smart software development involves splitting the system up into components so that each component only talks to the others through a narrow interface. This way you can easily pinch a component off from the the rest of the system, feed it some mock inputs and see if it gives the correct answers. 

This is difficult in RL systems. In RL systems, each component typically consumes a large number of mega- of gigabyte arrays and returns the same. The components are also unavoidably stateful, with the principal two components - the actor and learner - hefting around the state of the environnment and the network weights respectively. State can be thought of an interface with the own component's past, and in RL this interface is *huge*. 

Consequently while you *can* isolate components in RL (and we'll talk about how to below), it's much more painful to do than it is in other kinds of software.

**There are few black boxes**: A black box is a component that works in a complex way, but which you can reason about in a simple way. Another name for a black box would be 'a good abstraction'. The prototypical example is your computer: there's a hierarchy of concepts in there, from doped silicon through to operating systems, but as far as you the programmer are concerned it's all about for loops and function calls. 

RL has surprisingly few of these black boxes. You're required to know how your environment works, how your network works, how your optimizer works, how backprop works, how multiprocessing works, how stat collection and logging work. How GPUs work! There are [lots](https://docs.ray.io/en/latest/rllib.html) of [attempts](https://github.com/thu-ml/tianshou) at [writing](https://github.com/deepmind/acme) black-box [RL](https://github.com/astooke/rlpyt) libraries, but as of Jan 2021 my experience has been that these libraries have yet to be both flexible *and* easy to use. This might be a symptom of my odd strand of research, but I've heard several other researchers echo my frustrations.

### We're bad at writing RL systems
**Your expectations suck**: In any domain, problems evaporate as you get used to them. The first stack trace you see in your life is a nightmare; the millionth a triviality. All of the problems with RL listed above are only really problems because people new to the field expect something much more refined and reliable, as they've come to expect from other fields of programming and numerical research. If instead you arrive in RL expecting a garbage fire, you might just stay zen throughout.  

Obviously though, this begs the question of *why* RL development is a garbage fire.

**The community is young**: While reinforcement learning as a field stretches back decades, it has *exploded* in the past few years and continues apace today. Finding good abstractions requires in part that the userbase's requirements stabilize, and that just isn't the case yet. Some of that is because it's very much a community of researchers rather than a community of practitioners, and the terrible thing about researchers it that they're very keen on doing new and different things. Maybe it'll be different once someone figures out how to turn RL into an industry. 

**The community has other priorities**: Again, the community is a community of researchers. The population sets the priorities, and the priority is publication. Reliable, reproducible research contributes to publishing high-impact papers, but it also costs time and effort that is arguably better spent working on something *new*. And, well, it's hard to argue with the results: the current standards of RL development have carried us [a](https://deepmind.com/blog/article/muzero-mastering-go-chess-shogi-and-atari-without-rules) [long](https://openai.com/blog/learning-dexterity/) [way](https://deepmind.com/blog/article/AlphaStar-Grandmaster-level-in-StarCraft-II-using-multi-agent-reinforcement-learning). 

Don't take this as a clarion call for better practices, nor a stalwart defense of practices as they are. It's not a hill I wish to die on. I'm only giving an explanation for why things are the way they are, rather than a justification for it. My preferences are towards improved practices, but I can see the sense in the other side's position.

## Debugging Strategies

### Focus your efforts
### Localise your errors
### Maximise detection rate

# Practice

## Work from a reference implementation
*If you're new to reinforcement learning, writing things from scratch is the most catastrophically self-sabotaging thing you can do.*

There is an alluring masochism in writing things from scratch. There's concrete value in it too: by writing things from scratch, you're both forced to fully understand what you're doing and you're more likely to come up with a fresh perspective. In many other fields of software development these benefits would be worth the slow-down you suffer from having to work everything out yourself.

In reinforcement learning, these benefits are not worth it. At all. As discussed below, the nature of RL work makes it extremely hard for you to self-correct.

When I say 'use a reference implementation', there are several interpretations you can take depending on your risk tolerance. 
* The safest thing to do is to use a reference implementation out-of-the-box. Check that it works on your task, then repeatedly make a small change and check that it still works. 
* Less safe is to just use the reference implementation as a source of reliable components. Work to the same API, and check that giving your version of a component and their version give the same outputs.
* Least safe (but still dramatically better than going in blind) is to have one eye on the reference implementation while you write your own. Copy their hyperparameters, copy their discounting code, copy how they handle termination and invalid actions and a hundred other little things that you're likely to muck up otherwise. 

Here are some excellent reference implementations to choose from:
* [spinning-up](https://github.com/openai/spinningup) has been written by OpenAI, and has a [short course to go along with it](https://spinningup.openai.com/).
* [stable-baselines3](https://github.com/DLR-RM/stable-baselines3) is based on an older set of OpenAI implementations, but cleaned up and actively maintained.
* [cleanrl](https://github.com/vwxyzjn/cleanrl/tree/master/cleanrl) isolates every algorithm in its own file.
* [OpenSpiel](https://github.com/deepmind/open_spiel) is DeepMind's multi-agent reinforcement learning library. They provide both Python and C++ implementations of many algorithms - you'll probably want the Python ones.

## Assume you have a bug
When their RL implementation doesn't work, people are often keen to either (a) adjust their network architecture or (b) adjust their hyperparameters. On the other hand, they're reluctant to say they've got a bug.

Most often, it turns out they've got a bug.

Why bugs are so much more common in RL code is discussed below, but there's another advantage to assuming you've got a bug: bugs are a damn sight faster to find and fix than validating that your new architecture is an improvement over the old one. 

Now having said that you should assume you have a bug, it's worth mentioning that sometimes - rarely - you don't have a bug. What I'm advocating for here is not a blind faith in the buginess of your code, but for dramatically raising the threshold at which you start thinking 'OK, I think this is correct.'

## Loss curves are a red herring
When someone's RL implementation isn't working, they *luuuuuurv* to copy-paste a screenshot of their loss curve to you. They do this because they know they want a pretty, exponentially-decaying loss curve, and they know what they have *isn't that*.

The problem with using the loss curve as an indicator of correctness is somewhat that it's not reliable, but mostly because it doesn't localise errors. The shape of your loss curve says very little about where in your code you've messed up, and so says very little about what you need to change to get things working.

As in the previous section, my sweeping proclamation comes with some qualifiers. Once you have a semi-functional implementation and you've exhausted other, better methods of error localisation (as documented in the rest of this post), there *is* valuable information in a loss curve. If nothing else, being able to split a model's performance into 'how fast it learns' and 'where it plateaus' is a useful way to think about the next improvement you might want to make. But because it only offers *global* information about the performance of your implementation, it makes for a really poor debugging tool. 

## Unit test the tricky bits
Most of the bugs in a typical attempt at an RL implementation turn up in the same few places. Some of the usual suspects are

* reward discounting, especially around episode resets
* advantage calculations, again especially around resets
* buffering and batching, especially pairing the wrong rewards with the wrong observations

Fortunately, these components are all really easy to test! They've got none of the issues that validating RL algorithms as a whole has. These components are deterministic, they're easy to factor out, and they're fast. Checking you've got the termination right on your reward discounting is [a few lines](https://github.com/andyljones/megastep/blob/master/megastep/demo/learning.py#L134-L159).

What's even better is that most of the time, *as you write these things* you know you're messing them up. If you're not certain whether you've just accumulated the reward on one side of the reset or the other, *put a test in*. 

## Use probe environments.
The usual advice to people writing RL algorithms is to use a simple environment like the [classic control ones from the Gym](https://gym.openai.com/envs/#classic_control). 

Thing is, these envs have the same problem as looking at loss curves: at best they give you a noisy indicator, and if the noisy indicator looks poor you don't know *why* it looks poor. They don't localise errors.

Instead, construct environments that *do* localise errors. In a recent project, I used

1. **One action, zero observation, one timestep long, +1 reward every timestep**: This isolates the value network. If my agent can't learn that the value of the only observation it ever sees it 1, there's a problem with the value loss calculation or the optimizer.
2. **One action, zero observation, *two* timesteps long, +1 reward at the end**: If my agent can learn the value in (1.) but not this one, it must be that my reward discounting is broken.
3. **One action, random +1/-1 observation, one timestep long, obs-dependent +1/-1 reward every time**: If my agent can learn the value in (1.) but not this one - meaning it can learn a constant reward but not a predictable one! - it must be that backpropagation through my network is broken.
4. **Two actions, zero observation, one timestep long, action-dependent +1/-1 reward**: The first env to exercise the policy! If my agent can't learn to pick the better action, there's something wrong with either my advantage calculations, my policy loss or my policy update. That's three things, but it's easy to work out by hand the expected values for each one and check that the values produced by your actual code line up with them.
5. **Two actions, random +1/-1 observation, one timestep long, action-and-obs dependent +1/-1 reward**: Now we've got a dependence on both obs and action. The policy and value networks interact here, so there's a couple of things to verify: that the policy network learns to pick the right action in each of the two states, and that the value network learns that the value of each state is +1. If everything's worked up until now, then if - for example - the value network fails to learn here, it likely means your batching process is feeding the value network stale experience.
6. Etc.

You get the idea: (1.) is the simplest possible environment, and each new env adds the smallest possible bit of functionality. If the old env works but the successor doesn't, that gives you a *lot* of information about where the problem is. 

Even better, these environments are extraordinarily fast. When you've a correct implementation, it should only take a second or two to learn them. And they're *decisive*: if your value network in (1.) ends up more than an epsilon away from the correct value, it means you've got a bug.

As an aside, if you find yourself switching out envs a lot it makes sense to write your network with swappable 'heads': pass the `obs_space` and `action_space` of the env to your network's initializer, and let it nail on

* an intake that'll  transform samples from the obs space to flat vectors for your network to digest,
* an output that'll transform flat vectors from your network into the outputs the env expects.

This is an idea that's been developed a few times independently, though I can't remember where else I've seen it just this second. You can find my own (undocumented) implementation [here](https://github.com/andyljones/megastep/blob/23347dbc4698626408e4c5047c9f5b0a803c4e72/megastep/demo/heads.py#L69-L75).

## Use probe agents. 
In much the same way that you can simplify your environments to localise errors, you can do the same with your agents too. 
* Cheats
* Automatons
* Tabular

TODO: More of this.

## Log excessively.
The last three sections have involved controlled experiments of a sort, where you place your components in a known setup and see how they act. The complement to a controlled experiment is an observational study: watching your system in its natural habitat *very carefully* and seeing if you can spot anything anomalous.

In reinforcement learning, watching your system carefully means logging. Lots of logging. Below are some of the logs I've found particularly useful.

### Relative policy entropy 
The entropy of your policy network's outputs, relative to the maximum possible entropy. It'll usually start near 1, then rapidly fall for a while, then flatten out for the rest of training. 

If it stays very near 1, your agent is failing to learn any policy at all. You should check that your policy targets are being computed correctly, that the gradient's being backpropagated correctly, and - if you've defined a custom environment - then your environment is actually correct!

If it drops to zero or close to zero, then your agent has 'collapsed' into some - likely myopic - policy, and isn't exploring any more. This is usually because you'v either forgotten to include an exploration mechanism of some sort (like epsilon-greedy actions or an entropy term in the loss), or because your rewards are much larger than whatever you're using to encourage exploration. 

Sometimes it'll go up for a while; don't stress about that unless it's a large, permanent increase. If it *is* a large permanent increase and the minimum was very early in training, that can be an indicator that your policy fell into some myopic obviously-good behaviour that it's having to gradually climb back out of. It might help to turn up the exploration incentives. 

If the entropy oscillates wildly, that usually means your learning rate is too high.

### Kullback-Leibler divergence
The KL div between the policy that was used to collect the experience in the batch, and the policy that your learner's just generated for the same batch. This should be small but positive.

If it's very large then your agent is having to learn from experience that's very different to the current policy. In some algorithms - like those with a replay buffer - that's expected, and all that's important is the KL div is stable. In other algorithms (like PPO), a very large KL div is an indicator that the experience reaching your network is 'stale', and that'll slow down training.

If it's very low then that suggests your network hasn't changed much in the time since the experience was generated, and you can probably get away with turning the learning rate up. 

If it's growing steadily over time, that means you're probably feeding the same experience from early on in training back into the network again and again. Check your buffering system.

If it's negative - that shouldn't happen, and it means you're likely calculating the KL div incorrectly (probably by not handling invalid actions).

### Residual variance
The variance of (target values - network values), divided by the variance of the target values.

Like the policy entropy, this should start close to 1, fall very rapidly early on, and then decrease more gradually over the course of training. 

If it stays near 1, your value network isn't learning to predict the rewards. Check that your rewards are what you think they are, and check that your value loss and backprop through the value net are all working correctly. 

If it drops to zero, that's usually because the policy entropy has dropped to zero too, the policy has collapsed into some deterministic behaviour, and the value network has learned the rewards it is collecting perfectly. Another common reason is that some scenarios are generating vastly larger returns than the others, and the value net's learned to identify when that happens.

If the residual variance oscillates wildly, that usually means your learning rate is too high.

### Terminal correlation
The correlation between the value in the final state and the reward in the final step. This is only useful when there's lots of reward in the final step (like in boardgames). 

It should start near zero, rise rapidly, then plateau near 1. 

If it stays near zero but all the other value-related logs look good, then check that your reward-to-gos are being calculated correctly near termination! 

If reward is more evenly distributed through the episode, you could write a version of this that looks at the correlation of (next state's value - this state's value) with the reward in that step. I haven't used this myself though, so can't offer commentary. 

### Penultimate terminal correlation
The correlation between the value in the penultimate step and the final reward. Again, only useful when there's lots of reward at the end of the episode. If terminal correlation is high but penultimate terminal correlation is low, that's a strong indicator that your reward-to-gos aren't being carried backwards properly. 

### Value target distribution
Either plot a histogram, or the min/max/mean/std. The plots should indicate 'reasonable' value targets in the range \[-10, +10\] (and ideally  \[-3, +3\]). 

If they're larger than that, make your rewards proportionately smaller; if they're  smaller than that, make your rewards larger.

If they blow up, check that your reward discounting is correct, and possibly make your discount rate smaller. 

If they're blowing up but you're insistent on leaving the discount rate where it is, one alternative is to increase the number of steps used to bootstrap the value targets. In PPO, this'd mean using longer chunks. Longer chunks mean that the values used for bootstrapping get shrunk more before they're fed back to the value net as targets, increasing the stability. You could also consider annealing the discount factor from a smaller value up towards 1. 

### Reward distribution
Again, as a histogram or min/max/mean/std. What a reasonable reward distribution is depends on the environment; some envs have a few large rewards, while others have lots of small rewards. Either way, if it doesn't match your expectations then you should investigate.

### Value distribution
Again, as a histogram or min/max/mean/std. This is a complement to the previous two distributions and *should* closely match the value target distribution. If it doesn't, and it stays different from the value target distribution, that's an indicator that your value network is having trouble learning. 

It's also worth keeping an eye on the sign of the distribution. If your env only produces positive rewards but there are persistently negatives values in the value target distribution, that suggests your reward-to-go mechanism is badly broken or your value network is failing to learn. 

### Advantage distribution
Again, as a histogram or min/max/mean/std. As with the value targets, these should be in the range \[-10, +10\] (and ideally \[-3, +3\]). 

Advantages should also be approximately mean-zero due to how they're constructed; if they're persistently not then you've messed up your advantage calculations.

### Episode length distribution
Again, as a histogram or a min/max/mean/std. As with the reward distribution, interpreting this depends on the environment. If your environment should have arbitrary-length episodes, but you're seeing that every episode here is length 7, that indicates your environment is broken or your network's fallen into some degenerate behaviour.

### Sample staleness
Sample staleness is the number of learner steps between the network used to generate a sample, and the network currently learning from that sample. You can generate this by setting an 'age' attribute on the network, and incrementing it at every learner step. Then when a sample arrives at the learner, diff it against the learner's current age. 

How to interpret this depends on the algorithm, but it should generally stay at a steady value throughout training. In on-policy algorithms, lower sample stalenesses are better; in off-policy algorithms it's a tradeoff between fresh samples that let the network bootstrap quickly, and aged samples that stabilise things. 

### Step statistics
Step statistics are the abs-max and mean-square-value of the difference between the network's parameters when it enters the learner, and the network's parameters when it leaves the learner. 

Interpreting this depends on a whole bunch of things, but the mean-square value should typically be very small (1e-3 in my current training run with a LR of 1e-2), while the abs-max should small yet substantially larger than the mean-square-value. 

If the statistics are much smaller than that, you might be able to increase your learning rate; if they're much larger than that then be on the lookout for instability in your training.

### Gradient statistics
Gradient statistics re the abs-max and mean-square-value of the gradient. In the age of Adam and other quasi-Newton optimizers, this isn't as informative as it once was, because normalising by the curvature estimates can dramatically inflate or collapse the gradient. 

That said, if the step statistics are looking strange, this can help diagnose whether the problem is with the gradient calculation or with Adam's second-order magic. 

### Gradient noise
This is from [McCandlish and Kaplan](https://arxiv.org/abs/1812.06162), and it's intended to help you choose your batch size. Unfortunately it's *spectacularly* noisy, to the point where you likely want to average over all steps in your run. 

I've been thinking that it might be possible to get more stable estimates of the gradient noise from Adam's moment estimates, but that's decidedly on the to-do list. 

### Component throughput
At the least, the actor throughput and learner in terms of samples per second and steps per second. 

Typically the actor should be generating *at most* as many samples as the learner is consuming. If the actor is generating excess samples there are weak reasons that might be a good thing - it'll refresh the replay buffer more rapidly - but typically it's considered a waste of compute.

More generally, you want to see these remain stable throughout training. If they gradually decay, you're accumulating some costly state somewhere in your system. 

(For me, problems with gradually-slowing-down systems have always turned out to be with stats and logging, but I suspect that's because I've rolled my own stats and logging systems)

### Value trace
The trace of the value over a random episode from recent history, plotted together with the rewards. This can be useful if you suspect your value function or rewards of 'being weird' in some way; the value trace should typically be a collection of exponentially-increasing curves leading up to rewards, followed by vertical drops as the agent collects those rewards.

### GPU stats
There are several GPU-related stats that are worth tracking. First are the memory stats, which in PyTorch include
* the *memory allocation*, as reported by `torch.cuda.max_memory_allocated`. This is how much memory has actually been *used* by your computations,
* the *memory reserve*, as reported by `torch.cuda.max_memory_reserved`. This is how much memory PyTorch has *set aside* for your computations,
* the *memory gross*, as reported by `nvidia-smi`. This is how much memory PyTorch is using overall, [including the ~gigabyte it needs for its own kernels](https://github.com/pytorch/pytorch/issues/20532#issuecomment-540628939). It's this figure that'll crash your program if it hits the GPU's memory limit.
 
Keeping track of all three is useful for diagnosing memory issues: figuring out if it's you that's hanging onto too many tensors, or PyTorch that's being too aggressive with its caching.

If you're running out of memory and you can't immediately figure out why, [memlab](https://github.com/Stonesjtu/pytorch_memlab#memory-profiler) can help a lot. Disclosure: I wrote the frontend. 

As well as the memory stats, it's also useful to track the utilization, fan speed and temperature reported by `nvidia-smi`. You can get these values in [machine-readable form](https://github.com/andyljones/megastep/blob/master/rebar/stats/gpu.py#L17-L29).

In particular, if the utilization is persistently low then you should profile your code. Make sure to set `CUDA_LAUNCH_BLOCKING=1` before importing your tensor library, and then use [snakeviz](https://jiffyclub.github.io/snakeviz/) or [tuna](https://github.com/nschloe/tuna) to profile things in a broad way. If that's not enough detail, you can dig into things further with [nsight](https://developer.nvidia.com/nsight-systems). 
	
### Env-dependent metrics
TODO

### Traditional metrics
As well as the above, I also plot some other things out of habit

* **Reward per trajectory**: should increase dramatically at the start of training. This is, usually, what you care about. Unfortunately it's incredibly noisy and does little to localise errors. Closely related is the **reward per step**, which is typically what you care about in infinite environments.

* **Mean value**: is (if your value network is working well) a less-noisy proxy for the reward per trajectory. If your trajectories are particularly long compared to your reward discount factor however, this can be dramatically different from the reward per trajectory.

* **Policy and value losses**: should fall dramatically at the start of training, then level out.

# Theory




# A Broad Framework

