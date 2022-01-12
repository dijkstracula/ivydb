# IvyDB

Introspection-based driver for [IVy](https://github.com/kenmcmil/ivy/) programs

# Requirements

* Clang and LLDB
* IVy, with the 2to3 patches applied
* Python 3.x

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

1) Install ivy-db dependencies.

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

2) Set up Ivy.

`ms-ivy` is not explicitly a dependency because we may wish to either install
a stock release of Ivy or use a version checked out from source.  Let's do
the latter; clone the python3 port of Ivy (such as my [WIP
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

3) Tags.

Lastly, set up a tags file that knows about ivy, z3, and this project.

```
(venv) $ ctags -L<(find ~/code/ivy/ivy/)
(venv) $ ctags --append -R ./ivydb/
```

# Testing

```bash
$ python -m unittest
```

# Running

## Source <-> Ivy <-> C++ runtime mappings

Trivially, so far we can extract all external actions from an Ivy isolate,
figure out the C++ methods that they correspond to in the transpiled source
files, and the starting PC addresses in the compiled executable.

```bash
$ python ./ivydb -i ~/school/phd/projects/ivy_synthesis/sandbox -p echo
client.sock.recv(V0:client_id) is echo::ext__client__sock__recv(int, echo::tcp__endpoint, echo::msg_t) at 0x100007054
client.server.ping(V0:server_id) is echo::ext__client__server__ping(int, int, unsigned int) at 0x100008750
client.server.sock.recv(V0:server_id) is echo::ext__client__server__sock__recv(int, echo::tcp__endpoint, echo::msg_t) at 0x100007eec
```

## Generating Z3 constraints for an action

We can also extract preconditions and postconditions for actions.
