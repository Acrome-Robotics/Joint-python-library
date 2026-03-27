import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from kinematics import Robot4DOF

class Robot3DWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.robot = Robot4DOF()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Matches GUI theme background
        self.fig = plt.Figure(figsize=(5, 5))
        self.fig.patch.set_facecolor('#1c1d27') 
        self.canvas = FigureCanvas(self.fig)
        layout.addWidget(self.canvas)
        
        self.ax = self.fig.add_subplot(111, projection='3d')
        self.ax.set_facecolor('#1c1d27')
        
        # Style the axes
        self.ax.tick_params(colors='#94a3b8')
        self.ax.xaxis.label.set_color('#94a3b8')
        self.ax.yaxis.label.set_color('#94a3b8')
        self.ax.zaxis.label.set_color('#94a3b8')
        
        for pane in [self.ax.xaxis.pane, self.ax.yaxis.pane, self.ax.zaxis.pane]:
            pane.fill = False
            pane.set_edgecolor('#2e2f3e')
            
        self.ax.grid(color='#2e2f3e')
        
        self.current_q = [0.0, 0.0, 0.0, 0.0]
        self.target_pos = None
        self.update_plot(self.current_q)

    def update_plot(self, q=None, target_pos=None):
        """Redraws the robot given joint angles. Angles are in degrees."""
        if q is not None:
            self.current_q = q
        if target_pos is not None:
            self.target_pos = target_pos
            
        self.ax.clear()
        
        # Re-apply styles after clear
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        self.ax.set_zlabel('Z')
        for pane in [self.ax.xaxis.pane, self.ax.yaxis.pane, self.ax.zaxis.pane]:
            pane.fill = False
            pane.set_edgecolor('#2e2f3e')
            
        # Plot limits (~350mm max reach)
        limit = 350
        self.ax.set_xlim([-limit, limit])
        self.ax.set_ylim([-limit, limit])
        self.ax.set_zlim([0, limit])
        
        # Forward kinematics
        positions = self.robot.get_positions(self.current_q)
        
        # Unpack x, y, z
        xs = positions[:, 0]
        ys = positions[:, 1]
        zs = positions[:, 2]
        
        # Draw links and joints
        self.ax.plot(xs, ys, zs, 'o-', color='#a78bfa', linewidth=4, markersize=6)
        
        # Mark base origin clearly
        self.ax.plot([0], [0], [0], 'ko', markersize=8)
        
        # Draw target if set and not reached
        if self.target_pos is not None:
            tx, ty, tz = self.target_pos
            self.ax.plot([tx], [ty], [tz], 'rx', markersize=10, markeredgewidth=2)
            
        self.canvas.draw()
