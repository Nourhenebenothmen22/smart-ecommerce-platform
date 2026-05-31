import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useMyOrders } from '../../hooks/api/useOrders';
import { useAuth } from '../../contexts/AuthContext';
import { userService } from '../../services/userService';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { Tabs } from '../../components/ui/Tabs';
import { Card, CardHeader, CardTitle, CardBody } from '../../components/ui/Card';
import { TableContainer, Table, TableHeader, TableBody, TableRow, TableHead, TableCell } from '../../components/ui/Table';
import { Badge } from '../../components/ui/Badge';
import { SectionLoader } from '../../components/shared/SectionLoader';
import { EmptyState } from '../../components/shared/EmptyState';
import { formatPrice, formatDate } from '../../lib/utils';

export const CustomerDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user, refreshUser } = useAuth();
  const { data: orders, isLoading: ordersLoading, refetch: refetchOrders } = useMyOrders();

  const [activeTab, setActiveTab] = useState('orders');
  const [profileForm, setProfileForm] = useState({
    firstName: user?.firstName || '',
    lastName: user?.lastName || '',
    phone: user?.phone || '',
  });

  const [updateLoading, setUpdateLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    setUpdateLoading(true);
    setSuccessMsg('');
    setErrorMsg('');

    try {
      await userService.updateMe(profileForm);
      await refreshUser();
      setSuccessMsg('Profile updated successfully!');
    } catch (err: any) {
      setErrorMsg(err.message || 'Could not update profile.');
    } finally {
      setUpdateLoading(false);
    }
  };

  const getStatusVariant = (status: string) => {
    switch (status) {
      case 'delivered':
      case 'completed':
        return 'success';
      case 'pending':
      case 'pending_phone_confirmation':
        return 'warning';
      case 'processing':
      case 'shipped':
        return 'primary';
      case 'cancelled':
      case 'refunded':
        return 'danger';
      default:
        return 'default';
    }
  };

  const tabs = [
    { id: 'orders', label: t('customer.orders', 'My Orders') },
    { id: 'profile', label: t('customer.profile', 'Profile Settings') },
  ];

  return (
    <div className="container" style={{ paddingBottom: '4rem', paddingTop: '2rem', textAlign: 'left' }}>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '2rem' }}>
        {t('customer.dashboard', 'Customer Dashboard')}
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '3rem' }}>
        {/* Navigation Sidebar Card */}
        <Card style={{ height: 'fit-content' }}>
          <div style={{ padding: '1.5rem', borderBottom: '1px solid rgb(var(--border) / 0.5)' }}>
            <h3 style={{ fontWeight: 700, fontSize: '1.05rem' }}>{`${user?.firstName} ${user?.lastName}`}</h3>
            <p style={{ fontSize: '0.8rem', color: 'rgb(var(--muted-foreground))' }}>{user?.email}</p>
            <Badge variant="primary" style={{ marginTop: '0.5rem' }}>
              {user?.role}
            </Badge>
          </div>
          <div style={{ padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  textAlign: 'left',
                  padding: '0.6rem 0.8rem',
                  fontSize: '0.875rem',
                  borderRadius: 'var(--radius)',
                  fontWeight: activeTab === tab.id ? 700 : 500,
                  backgroundColor: activeTab === tab.id ? 'rgb(var(--muted))' : 'transparent',
                  color: activeTab === tab.id ? 'rgb(var(--primary))' : 'rgb(var(--foreground))',
                  cursor: 'pointer',
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </Card>

        {/* Tab content area */}
        <div>
          {activeTab === 'orders' && (
            <div>
              <h2 style={{ fontSize: '1.25rem', fontWeight: 700, marginBottom: '1.25rem' }}>
                {t('customer.orderHistory', 'Order History')}
              </h2>

              {ordersLoading ? (
                <SectionLoader />
              ) : !orders || orders.length === 0 ? (
                <EmptyState
                  title={t('customer.noOrders', 'No Orders Found')}
                  message="You haven't placed any orders yet. Visit the catalog to start shopping."
                  actionLabel="Browse Products"
                  onAction={() => (window.location.href = '/products')}
                />
              ) : (
                <TableContainer>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Order ID</TableHead>
                        <TableHead>Date</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Payment Method</TableHead>
                        <TableHead>Total</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {orders.map((ord: any) => (
                        <TableRow key={ord.id}>
                          <TableCell style={{ fontWeight: 600 }}>#{ord.id}</TableCell>
                          <TableCell>{formatDate(ord.createdAt)}</TableCell>
                          <TableCell>
                            <Badge variant={getStatusVariant(ord.status)}>{ord.status.replace(/_/g, ' ')}</Badge>
                          </TableCell>
                          <TableCell style={{ textTransform: 'capitalize' }}>
                            {ord.payment_method.replace(/_/g, ' ')}
                          </TableCell>
                          <TableCell style={{ fontWeight: 700, color: 'rgb(var(--primary))' }}>
                            {formatPrice(
                              ord.items?.reduce((sum: number, it: any) => sum + (it.price_at_order || it.product?.price || 0) * it.quantity, 0) || 0
                            )}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              )}
            </div>
          )}

          {activeTab === 'profile' && (
            <Card style={{ maxWidth: '500px' }}>
              <CardHeader>
                <CardTitle>Profile Details</CardTitle>
                <p style={{ fontSize: '0.85rem', color: 'rgb(var(--muted-foreground))' }}>
                  Update your contact details below.
                </p>
              </CardHeader>
              <form onSubmit={handleProfileUpdate}>
                <CardBody style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                  {successMsg && (
                    <div style={{ padding: '0.75rem', backgroundColor: 'rgb(var(--success) / 0.1)', color: 'rgb(var(--success))', borderRadius: 'var(--radius)', fontSize: '0.85rem', fontWeight: 600 }}>
                      ✓ {successMsg}
                    </div>
                  )}
                  {errorMsg && (
                    <div style={{ padding: '0.75rem', backgroundColor: 'rgb(var(--danger) / 0.1)', color: 'rgb(var(--danger))', borderRadius: 'var(--radius)', fontSize: '0.85rem', fontWeight: 600 }}>
                      ⚠️ {errorMsg}
                    </div>
                  )}

                  <div style={{ display: 'flex', gap: '1rem' }}>
                    <Input
                      id="firstName"
                      type="text"
                      label="First Name"
                      value={profileForm.firstName}
                      onChange={(e) => setProfileForm({ ...profileForm, firstName: e.target.value })}
                      required
                    />
                    <Input
                      id="lastName"
                      type="text"
                      label="Last Name"
                      value={profileForm.lastName}
                      onChange={(e) => setProfileForm({ ...profileForm, lastName: e.target.value })}
                      required
                    />
                  </div>

                  <Input
                    id="phone"
                    type="tel"
                    label="Phone Number"
                    value={profileForm.phone}
                    onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                  />
                </CardBody>
                <div style={{ padding: '1.25rem', borderTop: '1px solid rgb(var(--border) / 0.5)', display: 'flex', justifyContent: 'flex-end' }}>
                  <Button type="submit" variant="primary" isLoading={updateLoading}>
                    {t('common.save', 'Save Changes')}
                  </Button>
                </div>
              </form>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
