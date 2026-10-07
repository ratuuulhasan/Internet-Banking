import { Outlet } from 'react-router-dom';
import AdminSidebar from '../components/AdminSidebar';

export default function AdminLayout() {
  return (
    <div className="d-flex">
      <AdminSidebar />
      <div className="flex-grow-1 p-3" style={{ backgroundColor: '#f8f9fa' }}>
        <Outlet />
      </div>
    </div>
  );
}