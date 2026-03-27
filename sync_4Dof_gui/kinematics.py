import numpy as np

def dh_matrix(theta_deg, d, a, alpha_deg, offset_deg=0.0):
    theta = np.radians(theta_deg + offset_deg)
    alpha = np.radians(alpha_deg)
    ct = np.cos(theta)
    st = np.sin(theta)
    ca = np.cos(alpha)
    sa = np.sin(alpha)
    return np.array([
        [ct, -st*ca,  st*sa, a*ct],
        [st,  ct*ca, -ct*sa, a*st],
        [ 0,     sa,     ca,    d],
        [ 0,      0,      0,    1]
    ])

class Robot4DOF:
    def __init__(self):
        # DH params: [d, a, alpha, offset]
        self.dh_params = [
            {'d': 79.0, 'a': 0.0,   'alpha': 90.0,  'offset': 0.0},
            {'d': 0.0,  'a': 225.0, 'alpha': 0.0,   'offset': 90.0},
            {'d': 0.0,  'a': 0.0,   'alpha': -90.0, 'offset': -90.0},
            {'d': 79.0, 'a': 0.0,   'alpha': 90.0,  'offset': 0.0}
        ]

    def forward_kinematics(self, q):
        """
        Calculates all transformation matrices from base to end_effector.
        Returns a list of 4x4 transformation matrices for each joint origin
        plus the end-effector.
        """
        matrices = [np.eye(4)] # Base frame
        T = np.eye(4)
        for i in range(4):
            # q index might be out of bounds if q is not length 4, but we assume it is
            angle = q[i] if i < len(q) else 0.0
            A = dh_matrix(
                angle, 
                self.dh_params[i]['d'], 
                self.dh_params[i]['a'], 
                self.dh_params[i]['alpha'], 
                self.dh_params[i]['offset']
            )
            T = T @ A
            matrices.append(T)
            
        return matrices

    def get_positions(self, q):
        """Returns the (X, Y, Z) positions of all joints, shape (5, 3)."""
        matrices = self.forward_kinematics(q)
        positions = [M[:3, 3] for M in matrices]
        return np.array(positions)

    def inverse_kinematics(self, target_pos, current_q, max_iter=200, tol=2.0, alpha=10.0):
        """
        Computes IK using simple Jacobian pseudoinverse.
        Only targets position (X, Y, Z).
        alpha is the learning rate step size.
        Returns the computed q array or current_q if failed.
        """
        q = np.array(current_q, dtype=float)
        target_pos = np.array(target_pos, dtype=float)
        
        for _ in range(max_iter):
            # Current positions
            matrices = self.forward_kinematics(q)
            current_pos = matrices[-1][:3, 3]
            
            error = target_pos - current_pos
            if np.linalg.norm(error) < tol:
                break
                
            # Compute numerical Jacobian
            J = np.zeros((3, 4))
            delta = 1e-4
            for j in range(4):
                q_step = q.copy()
                q_step[j] += delta
                pos_step = self.forward_kinematics(q_step)[-1][:3, 3]
                J[:, j] = (pos_step - current_pos) / delta
                
            # Update q
            J_pinv = np.linalg.pinv(J)
            delta_q = J_pinv @ error
            q += alpha * delta_q
            
            # Keep angles in -180 to 180 range
            q = (q + 180) % 360 - 180
            
        return q.tolist()
