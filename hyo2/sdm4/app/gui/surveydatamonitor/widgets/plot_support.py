import logging

logger = logging.getLogger(__name__)


class PlotSupport:
    font_size = 6
    plot_context = {
        'font.family': 'sans-serif',
        'font.sans-serif': ['Tahoma', 'Bitstream Vera Sans', 'Lucida Grande', 'Verdana'],
        'font.size': font_size,
        'figure.titlesize': font_size + 1,
        'axes.labelsize': font_size,
        'legend.fontsize': font_size,
        'xtick.labelsize': font_size - 1,
        'ytick.labelsize': font_size - 1,
        'axes.linewidth': 0.5,
        'axes.xmargin': 0.01,
        'axes.ymargin': 0.01,
        'lines.linewidth': 0.8,
        'grid.alpha': 0.2,
    }

    f_dpi = 120  # dots-per-inch
    f_sz = (4.5, 2.0)  # inches
    f_map_sz = (5.0, 3.5)  # inches
    draft_color = '#00cc66'
    tss_color = '#3385ff'
    avg_depth_color = '#ffb266'
