# Overview

IVy programs can be compiled with the `target=test` flag, which, instead of
presenting a REPL for a user to interact with, links in an automated
randomised test runner, which includes calls that modify "omniciscent" ghost
state and a model checker that ensures program invariants are not violated
during program execution.

In this setting, isolates (a language construct instantiating, for instance, a
node in a distributed protocol) still contain private state and communicate
via external channels such as sockets.

```
 ┌───────────────────────────────┐
 │ IVy test program     ┌─────┐  │
 │ ----------------     │Ghost│  │
 │ ┌───────┐ ┌───────┐  │state│  │
 │ │Isolate│ │Isolate│  └─────┘  │
 │ │       │ │       │           │
 │ └─┼─────┘ └──┼────┘  ┌─────┐  │
 │   │   ▲      │  ▲    │Model│  │
 │   │   │      │  │    │chkr │  │
 │   │   │      │  │    └─────┘  │
 └───┼───┼──────┼──┼─────────────┘
     │   └──────┘  │
     └─────────────┘
       localhost
       TCP sockets

A "full IVy" deployment: an `n`-node system is implemented with `n` independent
IVy isolates (analagous to an instantiated class) running concurrently within a
single OS process.
```

This centralisation of code and state results in a straightforward and
efficient runtime.  Ghost actions are merely function calls that mutate shared
state.  However, this setting has a few limitations.  Even though communication
between isolates will use OS-level network primitives, the runtime bundles all
concurrently-executing isolates into a single OS process.  This forces all
nodes to share the same compiled code, even though an external process
that speaks the same network protocol could certainly stand in for one or more
IVy isolates.

```
 ┌───────────────────────────────┐  ┌────────────────┐
 │ IVy test program     ┌─────┐  │  │External process│
 │                      │Ghost│  │  │    ┌───────┐   │
 │ ┌───────┐            │state│  │  │    │ impl  │   │
 │ │Isolate│            └▲──┬─┘  │  │    │       │   │
 │ │       │             │  │    │  │    │       │   │
 │ │ │     │             │  │    │  │    └──┬───▲┘   │
 │ └─┼───▲─┘            ┌┴──▼─┐  │  │       │   │    │
 │   │   │              │Model│  │  │       │   │    │
 │   │   │              │chkr │  │  │       │   │    │
 │   │   │              └─────┘  │  │       │   │    │
 └───┼───┼───────────────────────┴  ┴───────┼───┼────┘
     │   └──────────────────────────────────┴   ┤
     └──────────────────────────────────────────┘
               localhost TCP sockets

An "n-1 / 1" deployment: an external implemenation drives one node over the
same network interface while the remaining `n-1` IVy isolates behave as before
within the test program.  Notice the issue that the external process behaves
independently of, and is ultimately unaware of, ghost actions and ghost state.
```

An "n-1 / 1" deployment tests a non-IVy test node in tandem with the rest
of the test harness.  This external process could be an IVy implementation not
compiled with `target=test` but that isn't terribly interesting; one could
imagine a canonical, "production-ready" implementation of the same protocol
written in another language to make up the external instance.  Here, we can
think of the high-level IVy implementation as a sort of refinement of the
canonical implementation.

Since communication between isolates takes place over sockets, this scheme
technically works up until ghost state needs to be updated: the model checker
wlil observe a violated program invariant because the external process did not
update -- indeed, presumably has no idea about -- the appropriate ghost actions
that the IVy program _would_ have called.

So, a third piece of the puzzle is needed: there needs to be some common interface
where some combination of Ivy test processes and "production" processes can
harmoniously co-exist within a test suite without giving up the benefits of the
single-process model.  

Without making any major assumptions about the production process, a reasonable
"lowest-common denominator" interface to different implementations' code and
data is the process-level debug information emitted naturally at compile-time,
suggesting an "ivy-aware" debugger might be a reasonable way to square the
circle.  Language-specific extensions can be built atop these primitives: for
instance, for a Java-based production implementation, the debugger could talk
to the JVM through JVMTI instead of ptrace.

```
  ┌────────────────────────────────────────────────────┐
  │IVydb                                               │
  │  ┌────────────────────────────┐  ┌───────────────┐ │
  │  │ Ivy runtime interface      │  │  Prod i'face  │ │
  │  └──────────┐▲────────────────┘  └───────┐▲──────┘ │
  │             ││                           ││        │
  └─────────────┼┼───────────────────────────┼┼────────┴ 
  ┌─────────────┴┼────────────────┐  ┌───────┴┼────────┐
  │             ▼┘                │  │       ▼┘        │
  │ IVy test program     ┌─────┐  │  │ Prod-ready impl │
  │                      │Ghost│  │  │    ┌───────┐    │
  │ ┌───────┐            │state│  │  │    │  impl │    │
  │ │Isolate│            └▲──┬─┘  │  │    │       │    │
  │ │       │             │  │    │  │    │       │    │
  │ │ │     │             │  │    │  │    └──┬───▲┘    │
  │ └─┼───▲─┘            ┌┴──▼─┐  │  │       │   │     │
  │   │   │              │Model│  │  │       │   │     │
  │   │   │              │chkr │  │  │       │   │     │
  │   │   │              └─────┘  │  │       │   │     │
  │   │   │                       │  │       │   │     │
  └───┼───┼───────────────────────┴──┴───────┼───┼─────┘
      │   └──────────────────────────────────┴   ┤
      └──────────────────────────────────────────┘
        localhost TCP sockets
```

These boxes can -- and likely would be -- permeable, in that in the presence of
the introspection module it isn't clear that the model checker best lives in
the IVy test program, for instance.  That's an engineering matter, though.

# Things we might like this to do:

## Holistic deterministic execution

So long as the introspection tool knows how to find program entry points
(corresponding to client actions that the randomised tester would generate),
it can drive both Ivy and prod implementations into taking actions of its
choosing.  A trivial example here is deterministic replay, where the debugger,
with a pre-determined sequence of events for each node, can simply invoke
actions on each node in that order.  (We'd probably want to serialise process
execution here, too - I _assume_ that that's something we can do via ptrace?)

## Infer ghost state / mimic ghost action calls

We still haven't solved the problem of how the production-impl node ought to
update its ghost state without making ghost calls.  One way to punt would be to
say "we own all the code, so stick ghost calls in the impl in the right place
which the debugger will trap on", but it seems nice to think about ways in which
we can avoid this.   If the IVy implementation is a "hand-written refinement"
of the prod implementation, can we replay actions to both a prod and an ivy
implementation and update it that way?  Seems like in the presence of a buggy
prod implementation this would send us down the garden path, so probably not
precisely what we want.  Hmm.

## Process checkpointing for state rollback / state space exploration?

The IVy randomised tester strictly moves forward in time, but perhaps we could
envision a fancier model checker that requires backtracking search
(explicit-state model checking?  Checking some contrapositive?) or something.
Checkpointing process state might be a good way to assist with this.  This might
fault in either OS-specific stuff or requring us to move up a layer of abstraction
if, say, data is sitting in unread kernel structures, though.  Hmm.

