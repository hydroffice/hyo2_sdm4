.. _how-to-contribute-label:

How to contribute
-----------------

Every open source project lives from the generous help by contributors that sacrifice their time and this is no different.

Public Repositories
===================

The source code is available on `GitHub`_.

To propose changes to Survey Data Monitor, you can follow the common Fork & Pull Request workflow.
If you are not familiar with such a workflow, a good starting point may be this `short tutorial`_.


Coding Style
============

To make participation as pleasant as possible, this project adheres to the `Code of Conduct`_ by the Python Software Foundation.

Here are a few hints and rules to get you started:

* Add yourself to the AUTHORS.txt_ file in an alphabetical fashion. Every contribution is valuable and shall be credited.
* If your change is noteworthy, add an entry to the changelog_.
* No contribution is too small; please submit as many fixes for typos and grammar bloopers as you can!
* Don't *ever* break backward compatibility.
* *Always* add tests and docs for your code. This is a hard rule; patches with missing tests or documentation won't be merged.
  If a feature is not tested or documented, it does not exist.
* Obey `PEP 8`_ and `PEP 257`_.
* Write `good commit messages`_.
* Ideally, `rebase and collapse`_ your commits, i.e. make your pull requests just one commit.

.. note::
   If you have something great but are not sure whether it adheres -- or even can adhere -- to the rules
   above: **please submit a pull request anyway**!
   In the best case, we can mold it into something, in the worst case the pull request gets politely closed.
   There's absolutely nothing to fear.

Thank you for considering to contribute! If you have any question or concerns, feel free to reach out to us.

Development Quick-start
=======================

Clone and install (in development mode) the `GitHub` repo:

* `git clone https://github.com/hydroffice/hyo2_sdm4.git`
* `pip install -e hyo2_sdm4`

The previous steps will also install all the required dependencies.

If you have issues installing `hyo2.abc2`_, you may want to:

* `git clone https://github.com/hydroffice/hyo2_abc2.git`
* `pip install -e hyo2_abc2`

If you have issues installing `hyo2.ssm2`_, you may want to:

* `git clone https://github.com/hydroffice/hyo2_soundspeed.git`
* `pip install -e hyo2_soundspeed`

For other issues installing dependencies (e.g., `GDAL`_), you may want to use `Anaconda`_.

Good references for a working dev env are:

* Windows: https://github.com/hydroffice/hyo2_sdm4/raw/refs/heads/master/.github/workflows/sdm_on_windows.yml
* Linux: https://github.com/hydroffice/hyo2_sdm4/raw/refs/heads/master/.github/workflows/sdm_on_linux.yml


.. _`short tutorial`: https://gist.github.com/giumas/67abeffcbf49d00703a57cbafac8b118
.. _`GitHub`: https://github.com/hydroffice/hyo2_sdm4
.. _`Code of Conduct`: http://www.python.org/psf/codeofconduct/
.. _`AUTHORS.txt`: https://github.com/hydroffice/hyo2_sdm4/raw/master/AUTHORS.rst
.. _`changelog`: https://github.com/hydroffice/hyo2_sdm4/raw/master/HISTORY.rst
.. _`PEP 8`: http://www.python.org/dev/peps/pep-0008/
.. _`PEP 257`: http://www.python.org/dev/peps/pep-0257/
.. _`rebase and collapse`: https://docs.gitlab.com/topics/git/git_rebase/
.. _`good commit messages`: http://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html
.. _`hyo2.abc2`: https://github.com/hydroffice/hyo2_abc2
.. _`hyo2.ssm2`: https://github.com/hydroffice/hyo2_soundspeed
.. _`GDAL`: https://github.com/OSGeo/gdal
.. _`Anaconda`: https://docs.anaconda.com/anaconda/install/
