:orphan:

###
API
###

.. currentmodule:: mne_nirs

.. toctree::

Experimental Design and Analysis
--------------------------------

.. currentmodule:: mne_nirs.experimental_design

.. automodule:: mne_nirs.experimental_design
   :no-members:
   :no-inherited-members:

.. autosummary::
   :toctree: generated/

   make_first_level_design_matrix
   create_boxcar


Preprocessing
-------------

Data quality evaluation.

.. currentmodule:: mne_nirs.preprocessing

.. automodule:: mne_nirs.preprocessing
   :no-members:
   :no-inherited-members:

.. autosummary::
   :toctree: generated/

   peak_power
   scalp_coupling_index_windowed


Signal Enhancement
------------------

.. currentmodule:: mne_nirs.signal_enhancement

.. automodule:: mne_nirs.signal_enhancement
   :no-members:
   :no-inherited-members:

.. autosummary::
   :toctree: generated/

   enhance_negative_correlation
   short_channel_regression


Statistics
----------

.. currentmodule:: mne_nirs.statistics

.. automodule:: mne_nirs.statistics
   :no-members:
   :no-inherited-members:

.. autosummary::
   :toctree: generated/

   run_GLM
   compute_contrast
   glm_region_of_interest
   statsmodels_to_results


Visualisation
------------------

fNIRS specific data visualisation.

.. currentmodule:: mne_nirs.visualisation

.. automodule:: mne_nirs.visualisation
   :no-members:
   :no-inherited-members:

.. autosummary::
   :toctree: generated/

   plot_nirs_source_detector


GLM result visualisation.

.. currentmodule:: mne_nirs.visualisation

.. automodule:: mne_nirs.visualisation
   :no-members:
   :no-inherited-members:
   :noindex:

.. autosummary::
   :toctree: generated/

   plot_glm_topo
   plot_glm_contrast_topo
   plot_glm_group_topo
   plot_glm_surface_projection


Data quality visualisation.

.. currentmodule:: mne_nirs.visualisation

.. automodule:: mne_nirs.visualisation
   :no-members:
   :no-inherited-members:
   :noindex:

.. autosummary::
   :toctree: generated/

   plot_timechannel_quality_metric


Simulation
----------

.. currentmodule:: mne_nirs.simulation

.. automodule:: mne_nirs.simulation
   :no-members:
   :no-inherited-members:

.. autosummary::
   :toctree: generated/

   simulate_nirs_raw


Channels
--------

Functions to help with handling channel information.

.. currentmodule:: mne_nirs.channels

.. automodule:: mne_nirs.channels
   :no-members:
   :no-inherited-members:

.. autosummary::
   :toctree: generated/

   get_short_channels
   get_long_channels
   picks_pair_to_idx


Utilities
---------

General helper functions.

.. currentmodule:: mne_nirs.utils

.. automodule:: mne_nirs.utils
   :no-members:
   :no-inherited-members:

.. autosummary::
   :toctree: generated/

   glm_to_tidy




Input/Output
------------

.. currentmodule:: mne_nirs.io.snirf

.. automodule:: mne_nirs.io.snirf
   :no-members:
   :no-inherited-members:

.. autosummary::
   :toctree: generated/

   write_raw_snirf
