# IvyDB

Introspection-based driver for [IVy](https://github.com/kenmcmil/ivy/) programs

# Overview

IVy programs can be compiled with the `target=test` flag, which, instead of
presenting a REPL for a user to interact with, links in an automated randomised
test runner, which includes calls that modify "omniciscent" ghost state and a
model checker that ensures program invariants are not violated during program
execution.

In this setting, isolates (a language construct instantiating, for instance, a
node in a distributed protocol) still contain private state and communicate via
external channels such as sockets.

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

# Requirements

* Clang and LLDB
* IVy?

# Setup

0) Install dependencies and venv.

Set up a virtual environment _for the version of python3 that LLDB expects_, to
ensure that our native bindings to the debugger work correctly.  On OSX, that
will be whatever the stock python3 interpreter is (3.8.8 for me, YMMV.) 

```
$ /usr/bin/python3 -m venv venv
$ source ./venv/bin/activate 
(venv) $ python --version
Python 3.8.9
(venv) $ 
```

Next, install the ivy-db dependencies (which are a superset of the ivy-language
dependencies; however, the legacy `setup.py` script in the Ivy repo w/r/t the
Z3 bindings on OSX seems weirdly broken on python3, owing to issues about not
being able to write into `/usr/`, but installing wheel and then installing
manually through pip seems to alleviate this issue.)  Building Z3 will take a
moment.

```
(venv) $ pip install wheel
...
Successfully installed wheel-0.37.0
(venv) $ pip install -r requirements.txt
...
Installing collected packages: tarjan, six, pydot, ply
Successfully installed ply-3.11 pydot-1.4.2 six-1.16.0 tarjan-0.2.3.2
```

`ms-ivy` is not explicitly a dependency because we may wish to either install a
stock release of Ivy or use a version checked out from source.  Let's do the
latter; clone the python3 port of Ivy (such as my [WIP
branch](https://github.com/dijkstracula/ivy/tree/nathan/python3_port)) and
install it.

```
(venv) $ pushd ~/code/ivy/
(venv) $ python setup.py develop
running develop
EasyInstallDeprecationWarning: easy_install command is deprecated. Use build and pip and other standards-based tools.
...
Using /Users/ntaylor/code/ivydb-py/venv/lib/python3.9/site-packages
Finished processing dependencies for ms-ivy==1.8.16
(venv) $ which ivyc
/Users/ntaylor/code/ivydb-py/venv/bin/ivyc
(venv) $ popd
(venv) $
```

Next we have a bunch of Z3 stuff to do.  Ivy uses a particular commit that is
known to work, and it's a submodule of the main Ivy repo.

```
(venv) $ pushd submodules/z3/src/api/python
```

One minor change: commit `4ac66dd80` is something, I think, we no longer want.
Back that change out.

```
(venv) $ python setup.py develop
...
Creating /Users/ntaylor/code/ivy/venv/lib/python3.8/site-packages/z3-solver.egg-link (link to .)
...
Finished processing dependencies for z3-solver==4.7.1.0
```

Ensure that in `src/api/python/z3/z3core.py`, line 13 is uncommented.

Lastly, set up a tags file that knows about ivy, z3, and this project.

```
(venv) $ ctags -L<(find ~/code/ivy/ivy/)
(venv) $ ctags --append -R .
```

# Testing

```bash
$ python -m unittest
```
# Running

Trivially, so far we can extract all external actions from an Ivy isolate,
figure out the C++ methods that they correspond to in the transpiled source
files, and the starting PC addresses in the compiled executable.

```bash
$ python ./ivydb -i ~/school/phd/projects/ivy_synthesis/sandbox -p echo
client.sock.recv(V0:client_id) is echo::ext__client__sock__recv(int, echo::tcp__endpoint, echo::msg_t) at 0x100007054
client.server.ping(V0:server_id) is echo::ext__client__server__ping(int, int, unsigned int) at 0x100008750
client.server.sock.recv(V0:server_id) is echo::ext__client__server__sock__recv(int, echo::tcp__endpoint, echo::msg_t) at 0x100007eec
```
