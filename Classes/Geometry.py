import numpy as np
import matplotlib.pyplot as plt
from .Plotting import *
from mpl_toolkits.mplot3d import Axes3D


class Airplane:
    def __init__(self,
                 name="Untitled Airplane",
                 xyz_ref=[0, 0, 0],
                 wings=[],
                 s_ref=1,
                 c_ref=1,
                 b_ref=1
                 ):
        self.name = name
        self.xyz_ref = np.array(xyz_ref)
        self.wings = wings
        self.s_ref = s_ref
        self.c_ref = c_ref
        self.b_ref = b_ref

    def draw(self,
             show=True,
             fig_to_plot_on=None,
             ax_to_plot_on=None
             ):

        # Setup
        if fig_to_plot_on == None or ax_to_plot_on == None:
            fig, ax = fig3d()
            fig.set_size_inches(12, 9)
        else:
            fig = fig_to_plot_on
            ax = ax_to_plot_on

        # TODO plot bodies

        # Plot wings
        for wing in self.wings:

            for i in range(len(wing.sections) - 1):
                le_start = wing.sections[i].xyz_le + wing.xyz_le
                le_end = wing.sections[i + 1].xyz_le + wing.xyz_le
                te_start = wing.sections[i].xyz_te() + wing.xyz_le
                te_end = wing.sections[i + 1].xyz_te() + wing.xyz_le

                points = np.vstack((le_start, le_end, te_end, te_start, le_start))
                x = points[:, 0]
                y = points[:, 1]
                z = points[:, 2]

                ax.plot(x, y, z, color='#cc0039')

                if wing.symmetric:
                    ax.plot(x, -1 * y, z, color='#cc0039')

        # Plot reference point
        x = self.xyz_ref[0]
        y = self.xyz_ref[1]
        z = self.xyz_ref[2]
        ax.scatter(x, y, z)

        set_axes_equal(ax)
        plt.tight_layout()
        if show:
            plt.show()

    def set_ref_dims_from_wing(self):
        pass
        # TODO set dims


class Wing:
    def __init__(self,
                 name="Untitled Wing",
                 xyz_le=[0, 0, 0],
                 sections=[],
                 symmetric=True,
                 incidence_angle=0
                 ):
        self.name = name
        self.xyz_le = np.array(xyz_le)
        self.sections = sections
        self.symmetric = symmetric
        self.incidence_angle = incidence_angle

    def area_wetted(self):
        # Returns the wetted area of a wing.
        area = 0
        for i in range(len(self.sections) - 1):
            chord_eff = (self.sections[i].chord
                         + self.sections[i + 1].chord) / 2
            this_xyz_te = self.sections[i].xyz_te()
            that_xyz_te = self.sections[i + 1].xyz_te()
            span_le_eff = np.hypot(
                self.sections[i].xyz_le[1] - self.sections[i + 1].xyz_le[1],
                self.sections[i].xyz_le[2] - self.sections[i + 1].xyz_le[2]
            )
            span_te_eff = np.hypot(
                this_xyz_te[1] - that_xyz_te[1],
                this_xyz_te[2] - that_xyz_te[2]
            )
            span_eff = (span_le_eff + span_te_eff) / 2
            area += chord_eff * span_eff
        if self.symmetric:
            area *= 2
        return area

    def area_projected(self):
        # Returns the area of the wing as projected onto the XY plane.
        area = 0
        for i in range(len(self.sections) - 1):
            chord_eff = (self.sections[i].chord
                         + self.sections[i + 1].chord) / 2
            this_xyz_te = self.sections[i].xyz_te()
            that_xyz_te = self.sections[i + 1].xyz_te()
            span_le_eff = np.abs(
                self.sections[i].xyz_le[1] - self.sections[i + 1].xyz_le[1]
            )
            span_te_eff = np.abs(
                this_xyz_te[1] - that_xyz_te[1]
            )
            span_eff = (span_le_eff + span_te_eff) / 2
            area += chord_eff * span_eff
        if self.symmetric:
            area *= 2
        return area

    def span(self):
        # Returns the span (y-distance between the root of the wing and the tip). If symmetric, this is doubled to obtain the full span.
        spans = []
        for i in range(len(self.sections)):
            spans.append(np.abs(self.sections[i].xyz_le[1] - self.sections[0].xyz_le[1]))
        span = np.max(spans)
        if self.symmetric:
            span *= 2
        return span

    def aspect_ratio(self):
        return self.span() ** 2 / self.area()


class WingSection:

    def __init__(self,
                 xyz_le=[0, 0, 0],
                 chord=0,
                 twist=0,
                 airfoil=[],
                 chordwise_panels=30,
                 chordwise_spacing="cosine",
                 spanwise_panels=30,
                 spanwise_spacing="cosine"
                 ):
        self.xyz_le = np.array(xyz_le)
        self.chord = chord
        self.twist = twist
        self.airfoil = airfoil
        self.chordwise_panels = chordwise_panels
        self.chordwise_spacing = chordwise_spacing
        self.spanwise_panels = spanwise_panels
        self.spanwise_spacing = spanwise_spacing

    def xyz_te(self):
        xyz_te = self.xyz_le + self.chord * np.array(
            [np.cos(np.radians(self.twist)),
             0,
             -np.sin(np.radians(self.twist))
             ])

        return xyz_te


class Airfoil:
    cached_airfoils = []

    def __init__(self,
                 name="naca0012"
                 ):
        self.name = name
        # TODO UNCOMMENT ME
        #  self.read_coordinates() # populates self.coordinates

        self.get_2D_aero_data() # populates self.aerodata

    def read_coordinates(self):
        # Try to read from file
        import importlib.resources
        from . import airfoils

        raw_text = importlib.resources.read_text(airfoils, self.name + '.dat')
        trimmed_text = raw_text[raw_text.find('\n'):]

        coordinates1D = np.fromstring(trimmed_text, sep='\n')  # returns the coordinates in a 1D array
        assert len(coordinates1D) % 2 == 0, 'File could not be read correctly!'  # Should be even

        coordinates = np.reshape(coordinates1D, (len(coordinates1D) // 2, 2))

        self.coordinates = coordinates

    def draw(self):
        # Get coordinates if they don't already exist
        try:
            self.coordinates
        except NameError:
            print("You must call read_coordinates() on an Airfoil before drawing it. Automatically doing that...")
            self.read_coordinates()

        plt.plot(self.coordinates[:,0],self.coordinates[:,1])
        plt.xlim((-0.05, 1.05))
        plt.ylim((-0.5, 0.5))
        plt.axis('equal')

    def get_2D_aero_data(self):
        pass
        # TODO do this

    def compute_mean_camber_line(self):
        pass
    #TODO do this

    def get_point_on_chord_line(self, chordfraction):
        return np.array([chordfraction,0])

    def get_point_on_camber_line(self, chordfraction):
        pass