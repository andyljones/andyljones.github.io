---
title: Debugging Reinforcement Learning Systems
description: How to debug your reinforcement learning implementations, without the agonizing pain 
date: 2021/01/01
category: Technical
publish: False
---
**This is still a draft. If you come across it somehow, please do not share it until it's complete**

Debugging reinforcement learning algorithms is extremely hard. You might think 'yes, but I'm very smart!'. Well, [here's the (now) head of Tesla's AI division taking six weeks to write a from-scratch policy gradients implementation, despite having all of OpenAI's expertise available to him](https://news.ycombinator.com/item?id=13519044). 

I am not as good a machine learning researcher as Andrej Karpathy, and I say with  confidence you aren't either. 

You should expect to spend orders of magnitude longer debugging and validating your algorithm than you do writing it in the first place. If this is your first time, you might plausibly have a few hundred lines of code that you *think* are correct in an hour, and a system that's *actually* correct two months later.

# Concrete Advice

With that in mind, let's discuss some ways to make the misery of debugging less miserable. I've put this advice in priority order.

## 1. Work from a reference implementation
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

## 2. Assume you have a bug
When their RL implementation doesn't work, people are often keen to either (a) adjust their network architecture or (b) adjust their hyperparameters. On the other hand, they're reluctant to say they've got a bug.

Most often, it turns out they've got a bug.

Why bugs are so much more common in RL code is [[RL Debugging Without the Agonizing Pain#Your Intuition Sucks|discussed below]], but there's another advantage to assuming you've got a bug: bugs are a damn sight faster to find and fix than validating that your new architecture is an improvement over the old one. 

Now having said that you should assume you have a bug, it's worth mentioning that sometimes - rarely - you don't. What I'm advocating for here is not a blind faith in the buginess of your code, but for dramatically raising the threshold at which you start thinking 'OK, I think this is correct.'

## 3. Stop looking at your loss curves
When someone's RL implementation isn't working, they *luuuuuurv* to copy-paste a screenshot of their loss curve to you. They do this because they know they want a pretty, exponentially-decaying loss curve, and they know what they have *isn't that*.

The problem with using the loss curve as an indicator of correctness is somewhat that it's not reliable, but mostly because it doesn't localise errors. The shape of your loss curve says very little about where in your code you've messed up, and so says very little about what you need to change to get things working.

As in the previous section, my sweeping proclamation comes with some qualifiers. Once you have a semi-functional implementation and you've exhausted other, better methods of error localisation (as documented in the rest of this post), there *is* valuable information in a loss curve. 

If nothing else, being able to split a model's performance into 'how fast it learns' and 'where it plateaus' is a useful way to think about the next improvement you might want to make. But because it only offers *global* information about the performance of your implementation, it makes for a really shitty debugging tool. 

## 4. Test out the tricky bits
Most of the bugs in a typical attempt at an RL implementation turn up in the same few places. Some of the usual suspects are

* reward discounting, especially around episode resets
* advantage calculations, again especially around resets
* buffering and batching, especially pairing the wrong rewards with the wrong observations

Fortunately, these components are all really easy to test! They've got none of the issues that validating RL algorithms as a whole has. These components are deterministic, they're easy to factor out, and they're fast. Checking you've got the termination right on your reward discounting is [a few lines](https://github.com/andyljones/megastep/blob/master/megastep/demo/learning.py#L134-L159).

What's even better is that most of the time, *as you write these things* you know you're messing them up. If you're not certain whether you've just accumulated the reward on one side of the reset or the other, *put a test in*. 

## 5. Use simpler environments. No, even simpler than that.
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

## 6. Use simple agents. No, even simpler than that. 
In much the same way that you can simplify your environments to localise errors, you can do the same with your agents too. 
* Cheats
* Automatons
* Tabular

TODO: More of this.

## 7. Log *everything*
The last three sections have involved controlled experiments of a sort, where you place your components in a known setup and see how they act. The compliment to a controlled experiment is an observational study: watching your system in its natural habitat *very carefully* and seeing if you can spot anything anomalous.

In reinforcement learning, watching your system carefully means logging. Lots of logging. Logs that I've found particularly useful are

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


# Why is debugging RL so hard?
As with many 'failures', the overall pain [is a product of many small pains](https://en.wikipedia.org/wiki/Swiss_cheese_model). Many of these pains are shared by other kinds of systems, but reinforcement learning is rare in having them all in one place.

### Failure is hidden
**Everything has to work for anything to work**:
**Performance is noisy**: 

### Simplifying is hard
**There're no good interfaces**:
**There are no good black boxes**:

### You are bad at writing RL systems
**Your intuition sucks**:
**Your expectations suck**:

### Everyone else is bad at writing RL systems
**The community is young**:
**The community has other priorities**:


# A Broad Framework

* Focus your efforts
* Localise your errors
* Maximise detection rate

#notes-blogposts 