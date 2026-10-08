import { useEffect, useState } from 'react';
import { Card, Table, Badge, Button, Form, InputGroup, Modal, Spinner } from 'react-bootstrap';
import { toast } from 'react-toastify';
import { adminApi } from '../../api/admin';

export default function Users() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [showRole, setShowRole] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [newRole, setNewRole] = useState('');

  const load = () => {
    setLoading(true);
    adminApi.listUsers({ search, role: roleFilter, status: statusFilter })
      .then(r => setUsers(r.data.results || r.data))
      .catch(() => toast.error('Failed to load users'))
      .finally(() => setLoading(false));
  };

  useEffect(load, [search, roleFilter, statusFilter]);

  const toggleBlock = async (u) => {
    if (!window.confirm(`${u.status === 'BLOCKED' ? 'Unblock' : 'Block'} this user?`)) return;
    try {
      if (u.status === 'BLOCKED') {
        await adminApi.unblockUser(u.user_id);
        toast.success('User unblocked');
      } else {
        await adminApi.blockUser(u.user_id);
        toast.success('User blocked');
      }
      load();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Action failed');
    }
  };

  const openRoleModal = (u) => {
    setCurrentUser(u);
    setNewRole(u.role);
    setShowRole(true);
  };

  const saveRole = async () => {
    try {
      await adminApi.changeRole(currentUser.user_id, newRole);
      toast.success('Role updated');
      setShowRole(false);
      load();
    } catch {
      toast.error('Failed to change role');
    }
  };

  return (
    <div className="container-fluid mt-4">
      <h2>👥 User Management</h2>

      <Card className="mt-3">
        <Card.Body>
          <div className="d-flex gap-2 mb-3">
            <InputGroup>
              <Form.Control
                placeholder="Search by name, email, phone"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </InputGroup>
            <Form.Select style={{ width: 180 }} value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}>
              <option value="">All Roles</option>
              <option>CUSTOMER</option>
              <option>ADMIN</option>
              <option>EMPLOYEE</option>
              <option>AUDITOR</option>
            </Form.Select>
            <Form.Select style={{ width: 180 }} value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}>
              <option value="">All Status</option>
              <option>ACTIVE</option>
              <option>PENDING</option>
              <option>BLOCKED</option>
              <option>CLOSED</option>
            </Form.Select>
            <Button variant="primary" onClick={load}>🔄</Button>
          </div>

          {loading ? <Spinner animation="border" /> : (
            <Table striped hover responsive>
              <thead>
                <tr>
                  <th style={{ width: 60 }}>#</th>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Phone</th>
                  <th>Role</th>
                  <th>Status</th>
                  <th>Joined</th>
                  <th style={{ width: 160 }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u, index) => (
                  <tr key={u.user_id}>
                    <td><strong>{index + 1}</strong></td>
                    <td>{u.full_name}</td>
                    <td>{u.email}</td>
                    <td>{u.phone}</td>
                    <td><Badge bg="secondary">{u.role}</Badge></td>
                    <td>
                      <Badge bg={
                        u.status === 'ACTIVE' ? 'success' :
                        u.status === 'BLOCKED' ? 'danger' :
                        u.status === 'PENDING' ? 'warning' : 'dark'
                      }>{u.status}</Badge>
                    </td>
                    <td>{new Date(u.created_at).toLocaleDateString()}</td>
                    <td>
                      <Button size="sm"
                        variant={u.status === 'BLOCKED' ? 'success' : 'danger'}
                        onClick={() => toggleBlock(u)}>
                        {u.status === 'BLOCKED' ? 'Unblock' : 'Block'}
                      </Button>{' '}
                      <Button size="sm" variant="outline-primary"
                        onClick={() => openRoleModal(u)}>Role</Button>
                    </td>
                  </tr>
                ))}
                {users.length === 0 && !loading && (
                  <tr><td colSpan={8} className="text-center text-muted">No users found</td></tr>
                )}
              </tbody>
            </Table>
          )}
        </Card.Body>
      </Card>

      <Modal show={showRole} onHide={() => setShowRole(false)}>
        <Modal.Header closeButton><Modal.Title>Change Role</Modal.Title></Modal.Header>
        <Modal.Body>
          <p>User: <strong>{currentUser?.email}</strong></p>
          <Form.Select value={newRole}
            onChange={(e) => setNewRole(e.target.value)}>
            <option value="CUSTOMER">Customer</option>
            <option value="ADMIN">Admin</option>
            <option value="EMPLOYEE">Employee</option>
            <option value="AUDITOR">Auditor</option>
          </Form.Select>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowRole(false)}>Cancel</Button>
          <Button onClick={saveRole}>Save</Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}