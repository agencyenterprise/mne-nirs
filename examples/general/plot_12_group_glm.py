"""
.. _tut-fnirs-group:

Group Level GLM Analysis
========================

This is an example of a group level GLM based
functional near-infrared spectroscopy (fNIRS)
analysis in MNE-NIRS.

.. sidebar:: Relevant literature

   Luke, Robert, et al.
   "Analysis methods for measuring passive auditory fNIRS responses generated
   by a block-design paradigm." Neurophotonics 8.2 (2021):
   `025008 <https://www.spiedigitallibrary.org/journals/neurophotonics/volume-8/issue-2/025008/Analysis-methods-for-measuring-passive-auditory-fNIRS-responses-generated-by/10.1117/1.NPh.8.2.025008.short>`_.

   Santosa, H., Zhai, X., Fishburn, F., & Huppert, T. (2018).
   The NIRS brain AnalyzIR toolbox. Algorithms, 11(5), 73.

   Gorgolewski, Krzysztof J., et al.
   "The brain imaging data structure, a format for organizing and describing
   outputs of neuroimaging experiments." Scientific data 3.1 (2016): 1-9.

Individual level analysis of this data is described in the
:ref:`MNE fNIRS waveform tutorial <mne:tut-fnirs-processing>`
and the
:ref:`MNE-NIRS fNIRS GLM tutorial <tut-fnirs-hrf>`
So this example will skim over the individual level details
and focus on the group level aspect of analysis.
Here we describe how to process multiple measurements
and summarise  group level effects both as summary statistics and visually.

The data used in this example is available
`at this location <https://github.com/rob-luke/BIDS-NIRS-Tapping>`_.
It is a finger tapping example and is briefly described below.
The dataset contains 5 participants.
The example dataset is in
`BIDS <https://bids.neuroimaging.io>`_
format and therefore already contains
information about triggers, condition names, etc.

.. note::

   The BIDS specification for NIRS data is still under development. See:
   `fNIRS BIDS proposal <https://github.com/bids-standard/bids-specification/pull/802>`_.
   As such, you must use the development branch of MNE-BIDS.

   To install the fNIRS development branch of MNE-BIDS run:
   `pip install https://codeload.github.com/rob-luke/mne-bids/zip/nirs`

.. collapse:: |chevron-circle-down| Data description (click to expand)
   :class: success

   Optodes were placed over the motor cortex using the standard NIRX motor
   montage, but with 8 short channels added (see their web page for details).
   To view the sensor locations run
   `raw_intensity.plot_sensors()`.
   A sound was presented to indicate which hand the participant should tap.
   Participants tapped their thumb to their fingers for 5s.
   Conditions were presented in a random order with a randomised inter
   stimulus interval.

.. contents:: Page contents
   :local:
   :depth: 2
"""
# sphinx_gallery_thumbnail_number = 2

# Authors: Robert Luke <mail@robertluke.net>
#
# License: BSD (3-clause)


# Import common libraries
import numpy as np
import pandas as pd

# Import MNE processing
from mne.preprocessing.nirs import optical_density, beer_lambert_law

# Import MNE-NIRS processing
from mne_nirs.statistics import run_GLM
from mne_nirs.experimental_design import make_first_level_design_matrix
from mne_nirs.statistics import glm_region_of_interest, statsmodels_to_results
from mne_nirs.statistics import compute_contrast
from mne_nirs.channels import get_short_channels, get_long_channels
from mne_nirs.channels import picks_pair_to_idx
from mne_nirs.utils._io import glm_to_tidy
from mne_nirs.visualisation import plot_glm_group_topo
from mne_nirs.datasets import fnirs_motor_group
from mne_nirs.visualisation import plot_glm_surface_projection

# Import MNE-BIDS processing
from mne_bids import BIDSPath, read_raw_bids

# Import StatsModels
import statsmodels.formula.api as smf

# Import Plotting Library
import matplotlib.pyplot as plt
import matplotlib as mpl
from lets_plot import *
LetsPlot.setup_html()


###############################################################################
# Define individual analysis
# --------------------------
#
# .. sidebar:: Individual analysis procedures
#
#    :ref:`Waveform individual analysis <tut-fnirs-processing>`
#
#    :ref:`GLM individual analysis <tut-fnirs-hrf>`
#
# First we define the analysis that will be applied to each file.
# This is a GLM analysis as described in the
# :ref:`individual GLM tutorial <tut-fnirs-hrf>`,
# so this example will skim over the individual level details.
#
# The analysis extracts a response estimate for each channel,
# each region of interest, and computes a contrast between left and right
# finger tapping.
# We return the raw object and data frames for the computed results.
# Information about channels, triggers and their meanings are stored in the
# BIDS structure and are automatically obtained when importing the data.
#
# Here we also resample to a 0.3 Hz sample rate just to speed up the example
# and use less memory, resampling to 0.6 Hz is a better choice for full
# analyses.


def individual_analysis(bids_path, ID):

    raw_intensity = read_raw_bids(bids_path=bids_path, verbose=False)

    # Convert signal to haemoglobin and resample
    raw_od = optical_density(raw_intensity)
    raw_haemo = beer_lambert_law(raw_od)
    raw_haemo.resample(0.3)

    # Cut out just the short channels for creating a GLM repressor
    sht_chans = get_short_channels(raw_haemo)
    raw_haemo = get_long_channels(raw_haemo)

    # Create a design matrix
    design_matrix = make_first_level_design_matrix(raw_haemo, stim_dur=5.0)

    # Append short channels mean to design matrix
    design_matrix["ShortHbO"] = np.mean(sht_chans.copy().pick(picks="hbo").get_data(), axis=0)
    design_matrix["ShortHbR"] = np.mean(sht_chans.copy().pick(picks="hbr").get_data(), axis=0)

    # Run GLM
    glm_est = run_GLM(raw_haemo, design_matrix)

    # Define channels in each region of interest
    # List the channel pairs manually
    left = [[4, 3], [1, 3], [3, 3], [1, 2], [2, 3], [1, 1]]
    right = [[8, 7], [5, 7], [7, 7], [5, 6], [6, 7], [5, 5]]
    # Then generate the correct indices for each pair
    groups = dict(
        Left_Hemisphere=picks_pair_to_idx(raw_haemo, left, on_missing='ignore'),
        Right_Hemisphere=picks_pair_to_idx(raw_haemo, right, on_missing='ignore'))

    # Extract channel metrics
    cha = glm_to_tidy(raw_haemo, glm_est, design_matrix)
    cha["ID"] = ID  # Add the participant ID to the dataframe

    # Compute region of interest results from channel data
    roi = pd.DataFrame()
    for idx, col in enumerate(design_matrix.columns):
        roi = roi.append(glm_region_of_interest(glm_est, groups, idx, col))
    roi["ID"] = ID  # Add the participant ID to the dataframe

    # Contrast left vs right tapping
    contrast_matrix = np.eye(design_matrix.shape[1])
    basic_conts = dict([(column, contrast_matrix[i])
                        for i, column in enumerate(design_matrix.columns)])
    contrast_LvR = basic_conts['Tapping/Left'] - basic_conts['Tapping/Right']
    contrast = compute_contrast(glm_est, contrast_LvR)
    con = glm_to_tidy(raw_haemo, contrast, design_matrix)
    con["ID"] = ID  # Add the participant ID to the dataframe

    # Convert to uM for nicer plotting below.
    cha["theta"] = [t * 1.e6 for t in cha["theta"]]
    roi["theta"] = [t * 1.e6 for t in roi["theta"]]
    con["effect"] = [t * 1.e6 for t in con["effect"]]

    return raw_haemo, roi, cha, con


###############################################################################
# Run analysis on all participants
# --------------------------------
#
# Next we loop through the five measurements and run the individual analysis
# on each. We append the individual results in to a large dataframe that
# will contain the results from all measurements. We create a group dataframe
# for the region of interest, channel level, and contrast results.

df_roi = pd.DataFrame()  # To store region of interest results
df_cha = pd.DataFrame()  # To store channel level results
df_con = pd.DataFrame()  # To store channel level contrast results

for sub in range(1, 6):  # Loop from first to fifth subject
    ID = '%02d' % sub  # Tidy the subject name

    # Create path to file based on experiment info
    bids_path = BIDSPath(subject=ID, task="tapping",
                         root=fnirs_motor_group.data_path(),
                         datatype="nirs", suffix="nirs", extension=".snirf")

    # Analyse data and return both ROI and channel results
    raw_haemo, roi, channel, con = individual_analysis(bids_path, ID)

    # Append individual results to all participants
    df_roi = df_roi.append(roi)
    df_cha = df_cha.append(channel)
    df_con = df_con.append(con)


###############################################################################
# Visualise Individual results
# ----------------------------
#
# First we visualise the results from each individual to ensure the
# data values look reasonable.
# Here we see that we have data from five participants, we plot just the HbO
# values and observe they are in the expect range.
# We can already see that the control condition is always near zero,
# and that the responses look to be contralateral to the tapping hand.

grp_results = df_roi.query("Condition in ['Control', 'Tapping/Left', 'Tapping/Right']")
grp_results = grp_results.query("Chroma in ['hbo']")

ggplot(grp_results, aes(x='Condition', y='theta', color='ROI', shape='ROI')) \
    + geom_hline(y_intercept=0, linetype="dashed", size=1) \
    + geom_point(size=5) \
    + facet_grid('ID') \
    + ggsize(900, 350)


###############################################################################
# Compute group level results
# ---------------------------
#
# .. sidebar:: Relevant literature
#
#    For an introduction to mixed effects analysis see:
#    Winter, Bodo. "A very basic tutorial for performing linear mixed effects
#    analyses." arXiv preprint arXiv:1308.5499 (2013).
#
#    For a summary of linear mixed models in python
#    and the relation to lmer see:
#    :ref:`statsmodels docs <statsmodels:mixedlmmod>`
#
#    For a summary of these models in the context of fNIRS see section 3.5 of:
#    Santosa, H., Zhai, X., Fishburn, F., & Huppert, T. (2018).
#    The NIRS brain AnalyzIR toolbox. Algorithms, 11(5), 73.
#
# Next we use a linear mixed effects model to examine the
# relation between conditions and our response estimate (theta).
# Combinations of 3 fixed effects will be evaluated, ROI (left vs right),
# condition (control, tapping/left, tapping/right), and chromophore (HbO, HbR).
# With a random effect of subject.
# Alternatively, you could export the group dataframe (`df_roi.to_csv()`) and
# analyse in your favorite stats program.
#
# We do not explore the modeling procedure in depth here as topics
# such model selection and examining residuals are beyond the scope of
# this example (see relevant literature).
# Alternatively, we could use a robust linear
# model by using the code
# `roi_model = rlm('theta ~ -1 + ROI:Condition:Chroma', grp_results).fit()`.

grp_results = df_roi.query("Condition in ['Control','Tapping/Left', 'Tapping/Right']")

roi_model = smf.mixedlm("theta ~ -1 + ROI:Condition:Chroma",
                        grp_results, groups=grp_results["ID"]).fit(method='nm')
roi_model.summary()


###############################################################################
# Visualise group results
# -----------------------
#
# Now we can summarise the output of the second level model.
# This figure shows that the control condition has small responses that
# are not significantly different to zero for both HbO
# and HbR in both hemispheres.
# Whereas clear significant responses are show for the two tapping conditions.
# We also observe the the tapping response is
# larger in the contralateral hemisphere.
# Filled symbols represent HbO, unfilled symbols represent HbR.

df = statsmodels_to_results(roi_model)

ggplot(df.query("Chroma == 'hbo'"),
       aes(x='Condition', y='Coef.', color='Significant', shape='ROI')) \
    + geom_hline(y_intercept=0, linetype="dashed", size=1) \
    + geom_point(size=5) \
    + scale_shape_manual(values=[16, 17]) \
    + ggsize(900, 300) \
    + geom_point(data=df.query("Chroma == 'hbr'")
                 .query("ROI == 'Left_Hemisphere'"), size=5, shape=1) \
    + geom_point(data=df.query("Chroma == 'hbr'")
                 .query("ROI == 'Right_Hemisphere'"), size=5, shape=2)


###############################################################################
# Group topographic visualisation
# -------------------------------
#
# We can also view the topographic representation of the data
# (rather than the ROI summary above).
# Here we just plot the oxyhaemoglobin for the two tapping conditions.
# First we compute the mixed effects model for each channel (rather
# than region of interest as above).
# Then we pass these results to the topomap function.

fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(10, 10),
                         gridspec_kw=dict(width_ratios=[1, 1]))

# Cut down the dataframe just to the conditions we are interested in
ch_summary = df_cha.query("Condition in ['Tapping/Left', 'Tapping/Right']")
ch_summary = ch_summary.query("Chroma in ['hbo']")

# Run group level model and convert to dataframe
ch_model = smf.mixedlm("theta ~ -1 + ch_name:Chroma:Condition",
                       ch_summary, groups=ch_summary["ID"]).fit(method='nm')
ch_model_df = statsmodels_to_results(ch_model)

# Plot the two conditions
plot_glm_group_topo(raw_haemo.copy().pick(picks="hbo"),
                    ch_model_df.query("Condition in ['Tapping/Left']"),
                    colorbar=False, axes=axes[0, 0],
                    vmin=0, vmax=20, cmap=mpl.cm.Oranges)

plot_glm_group_topo(raw_haemo.copy().pick(picks="hbo"),
                    ch_model_df.query("Condition in ['Tapping/Right']"),
                    colorbar=True, axes=axes[0, 1],
                    vmin=0, vmax=20, cmap=mpl.cm.Oranges)

# Cut down the dataframe just to the conditions we are interested in
ch_summary = df_cha.query("Condition in ['Tapping/Left', 'Tapping/Right']")
ch_summary = ch_summary.query("Chroma in ['hbr']")

# Run group level model and convert to dataframe
ch_model = smf.mixedlm("theta ~ -1 + ch_name:Chroma:Condition",
                       ch_summary, groups=ch_summary["ID"]).fit(method='nm')
ch_model_df = statsmodels_to_results(ch_model)

# Plot the two conditions
plot_glm_group_topo(raw_haemo.copy().pick(picks="hbr"),
                    ch_model_df.query("Condition in ['Tapping/Left']"),
                    colorbar=False, axes=axes[1, 0],
                    vmin=-10, vmax=0, cmap=mpl.cm.Blues_r)
plot_glm_group_topo(raw_haemo.copy().pick(picks="hbr"),
                    ch_model_df.query("Condition in ['Tapping/Right']"),
                    colorbar=True, axes=axes[1, 1],
                    vmin=-10, vmax=0, cmap=mpl.cm.Blues_r)


###############################################################################
# Contrasts
# ---------
#
# Finally we can examine the difference between the left and right hand
# tapping conditions by viewing the contrast results
# in a topographic representation.

fig, axes = plt.subplots(nrows=1, ncols=1, figsize=(6, 6))
con_summary = df_con.query("Chroma in ['hbo']")

# Run group level model and convert to dataframe
con_model = smf.mixedlm("effect ~ -1 + ch_name:Chroma",
                        con_summary, groups=con_summary["ID"]).fit(method='nm')
con_model_df = statsmodels_to_results(con_model,
                                      order=raw_haemo.copy().pick(
                                          picks="hbo").ch_names)

plot_glm_group_topo(raw_haemo.copy().pick(picks="hbo"),
                    con_model_df, colorbar=True, axes=axes)


###############################################################################
#
# Or we can view only the left hemisphere for the contrast.
# And set all channels that dont have a significant response to zero.
#

plot_glm_group_topo(raw_haemo.copy().pick(picks="hbo").pick(picks=range(10)),
                    con_model_df, colorbar=True, threshold=True)


###############################################################################
# Cortical Surface Projections
# ----------------------------
#
# .. sidebar:: 3D plotting
#
#    Due to limitations with the cloud computing used to generate these
#    documents, the 3D plot will not appear in the online documentation.
#    However, when you run this code locally you will obtain a 3D head figure
#    simillar to what is shown in the tutorial:
#    `ECOG tutorial <https://mne.tools/dev/auto_tutorials/clinical/30_ecog.html#sphx-glr-auto-tutorials-clinical-30-ecog-py>`_.
#
# The topographic plots above can sometimes be difficult to interpret with
# respect to the underlying cortical locations. It is also possible to present
# the data by projecting the channel level GLM values to the nearest cortical
# surface. This can make it easier to understand the spatial aspects of your
# data. Note however, that this is not a complete forward model with photon
# migration simulations.
# In the figure below we project the group results from the two conditions
# to the cortical surface, and also present the contrast results in the same
# fashion.
# As in the topo plots above you can see that the activity is predominately
# contralateral to the side of finger tapping.


# Generate brain figure from data
clim = dict(kind='value', pos_lims=(0, 8, 11))
brain = plot_glm_surface_projection(raw_haemo.copy().pick("hbo"),
                                    con_model_df, clim=clim, view='dorsal',
                                    colorbar=True, size=(800, 700))
brain.add_text(0.05, 0.95, "Left-Right", 'title', font_size=16, color='k')

# Run model code as above
clim = dict(kind='value', pos_lims=(0, 11.5, 17))
for idx, cond in enumerate(['Tapping/Left', 'Tapping/Right']):

    # Run same model as explained in the sections above
    ch_summary = df_cha.query("Condition in [@cond]")
    ch_summary = ch_summary.query("Chroma in ['hbo']")
    ch_model = smf.mixedlm("theta ~ -1 + ch_name", ch_summary,
                           groups=ch_summary["ID"]).fit(method='nm')
    model_df = statsmodels_to_results(ch_model)

    # Generate brain figure from data
    brain = plot_glm_surface_projection(raw_haemo.copy().pick("hbo"),
                                        model_df, clim=clim, view='dorsal',
                                        colorbar=True, size=(800, 700))
    brain.add_text(0.05, 0.95, cond, 'title', font_size=16, color='k')


###############################################################################
# Table of channel level results
# ------------------------------
#
# Sometimes a reviewer wants a long table of results per channel.
# This can be generated from the statistics dataframe.

ch_summary = df_cha.query("Condition in ['Tapping/Left', 'Tapping/Right']")
ch_summary = ch_summary.query("Chroma in ['hbo']")

# Run group level model and convert to dataframe
ch_model = smf.mixedlm("theta ~ -1 + ch_name:Chroma:Condition",
                       ch_summary, groups=ch_summary["ID"]).fit(method='nm')

# Here we can use the order argument to ensure the channel name order
ch_model_df = statsmodels_to_results(ch_model,
                                     order=raw_haemo.copy().pick(
                                         picks="hbo").ch_names)
# And make the table prettier
ch_model_df.reset_index(drop=True, inplace=True)
ch_model_df = ch_model_df.set_index(['ch_name', 'Condition'])
ch_model_df
