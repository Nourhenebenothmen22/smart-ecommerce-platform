import React, { useMemo, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  AlertCircle,
  BarChart3,
  Bot,
  Boxes,
  BrainCircuit,
  FolderTree,
  LayoutDashboard,
  PackagePlus,
  ShoppingCart,
  Star,
  Tags,
  Users,
  WalletCards,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { useProducts } from '../../hooks/api/useProducts';
import { useCategories } from '../../hooks/api/useCategories';
import { useAllOrders } from '../../hooks/api/useOrders';
import { useUsers } from '../../hooks/api/useUsers';
import { useReviews } from '../../hooks/api/useReviews';
import { Card, CardBody, CardHeader, CardTitle } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Badge } from '../../components/ui/Badge';
import { Skeleton } from '../../components/ui/Skeleton';
import { Table, TableBody, TableCell, TableContainer, TableHead, TableHeader, TableRow } from '../../components/ui/Table';
import { EmptyState } from '../../components/shared/EmptyState';
import { ErrorState } from '../../components/shared/ErrorState';
import { formatDate, formatPrice } from '../../lib/utils';

const COLORS = ['#0f766e', '#14b8a6', '#f59e0b', '#6366f1', '#ef4444', '#64748b'];
const CATEGORY_COLORS = ['#0f766e', '#14b8a6', '#d8b24b', '#6366f1', '#f59e0b', '#8b5cf6', '#ef4444', '#64748b'];
const LOW_STOCK_THRESHOLD = 10;
const CHART_AXIS_STYLE = { fontSize: 12, fill: 'rgb(var(--muted-foreground))', fontWeight: 600 };
const CHART_TOOLTIP_STYLE = {
  backgroundColor: 'rgb(var(--card))',
  border: '1px solid rgb(var(--border))',
  borderRadius: 14,
  boxShadow: '0 18px 44px rgba(15,23,42,0.16)',
  color: 'rgb(var(--foreground))',
};
const CHART_LEGEND_STYLE = { paddingTop: 12, fontSize: 12, fontWeight: 700 };

type AdminTab = 'overview' | 'orders' | 'products' | 'users' | 'insights';

function asArray<T>(value: unknown): T[] {
  return Array.isArray(value) ? value as T[] : [];
}

function getOrderTotal(order: any) {
  const explicit = Number(order.total_amount ?? order.totalAmount ?? order.total ?? 0);
  if (explicit > 0) return explicit;
  return asArray<any>(order.items).reduce((sum, item) => {
    const price = Number(item.subtotal ?? 0) || Number(item.unit_price ?? item.price_at_order ?? item.product?.price ?? 0) * Number(item.quantity ?? 0);
    return sum + price;
  }, 0);
}

function getMonthKey(value: unknown) {
  const date = value ? new Date(String(value)) : new Date();
  if (Number.isNaN(date.getTime())) return 'N/A';
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
}

function statusVariant(status: string) {
  if (['delivered', 'completed', 'paid'].includes(status)) return 'success';
  if (['pending', 'pending_phone_confirmation', 'manual_review', 'on_hold'].includes(status)) return 'warning';
  if (['cancelled', 'refunded', 'failed'].includes(status)) return 'danger';
  return 'primary';
}

function shortLabel(value: unknown, max = 14) {
  const label = String(value ?? '');
  return label.length > max ? `${label.slice(0, max - 1)}…` : label;
}

const ChartCard: React.FC<{ title: string; children: React.ReactNode; note?: string; className?: string }> = ({ title, children, note, className }) => (
  <Card className={`admin-chart-card${className ? ` ${className}` : ''}`}>
    <CardHeader className="admin-chart-header">
      <CardTitle>{title}</CardTitle>
      {note && <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.8rem' }}>{note}</p>}
    </CardHeader>
    <CardBody className="admin-chart-body">{children}</CardBody>
  </Card>
);

function CategoryTooltip({ active, payload, total, t }: { active?: boolean; payload?: any[]; total: number; t: any }) {
  if (!active || !payload?.length) return null;
  const item = payload[0].payload;
  const count = Number(item.value ?? 0);
  const percent = total > 0 ? Math.round((count / total) * 100) : 0;

  return (
    <div className="admin-category-tooltip">
      <strong>{item.name}</strong>
      <span>{t('adminDashboard.chartKeys.products')}: {count}</span>
      <span>{percent}%</span>
    </div>
  );
}

const UnavailableCard: React.FC<{ title: string; message: string; icon?: React.ReactNode }> = ({ title, message, icon }) => (
  <Card>
    <CardBody style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
      <div
        style={{
          width: 42,
          height: 42,
          borderRadius: 12,
          display: 'grid',
          placeItems: 'center',
          background: 'rgb(var(--muted))',
          color: 'rgb(var(--muted-foreground))',
          flexShrink: 0,
        }}
      >
        {icon ?? <AlertCircle size={20} />}
      </div>
      <div>
        <h3 style={{ fontSize: '0.95rem', fontWeight: 800 }}>{title}</h3>
        <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.82rem', marginTop: 4 }}>{message}</p>
      </div>
    </CardBody>
  </Card>
);

export const AdminDashboard: React.FC = () => {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState<AdminTab>('overview');
  const productsQuery = useProducts({ limit: '100' });
  const categoriesQuery = useCategories();
  const ordersQuery = useAllOrders();
  const usersQuery = useUsers();
  const reviewsQuery = useReviews();

  const products = asArray<any>(productsQuery.data?.products);
  const categories = asArray<any>(categoriesQuery.data);
  const orders = asArray<any>(ordersQuery.data);
  const users = asArray<any>(usersQuery.data);
  const reviewsPayload = reviewsQuery.data as any;
  const reviews = asArray<any>(reviewsPayload?.reviews ?? reviewsPayload);

  const isLoading = productsQuery.isLoading || categoriesQuery.isLoading || ordersQuery.isLoading || usersQuery.isLoading || reviewsQuery.isLoading;
  const hasError = productsQuery.isError || categoriesQuery.isError || ordersQuery.isError || usersQuery.isError || reviewsQuery.isError;

  const analytics = useMemo(() => {
    const customers = users.filter((user) => user.role === 'customer');
    const revenueOrders = orders.filter((order) => !['cancelled', 'refunded'].includes(String(order.status)));
    const totalRevenue = revenueOrders.reduce((sum, order) => sum + getOrderTotal(order), 0);
    const pendingOrders = orders.filter((order) => String(order.status).includes('pending')).length;
    const lowStockProducts = products.filter((product) => Number(product.stock ?? 0) <= LOW_STOCK_THRESHOLD);

    const monthly = new Map<string, { month: string; sales: number; revenue: number; orders: number }>();
    orders.forEach((order) => {
      const month = getMonthKey(order.created_at ?? order.createdAt);
      const current = monthly.get(month) ?? { month, sales: 0, revenue: 0, orders: 0 };
      current.orders += 1;
      current.sales += asArray<any>(order.items).reduce((sum, item) => sum + Number(item.quantity ?? 0), 0);
      current.revenue += ['cancelled', 'refunded'].includes(String(order.status)) ? 0 : getOrderTotal(order);
      monthly.set(month, current);
    });

    const statuses = new Map<string, number>();
    orders.forEach((order) => statuses.set(String(order.status ?? 'unknown'), (statuses.get(String(order.status ?? 'unknown')) ?? 0) + 1));

    const topProducts = new Map<string, { name: string; quantity: number; revenue: number }>();
    orders.forEach((order) => {
      asArray<any>(order.items).forEach((item) => {
        const name = item.product_name ?? item.product_name_snapshot ?? item.product?.name ?? `#${item.product_id}`;
        const quantity = Number(item.quantity ?? 0);
        const current = topProducts.get(name) ?? { name, quantity: 0, revenue: 0 };
        current.quantity += quantity;
        current.revenue += Number(item.subtotal ?? 0) || quantity * Number(item.unit_price ?? item.price_at_order ?? 0);
        topProducts.set(name, current);
      });
    });

    const productsByCategory = new Map<string, number>();
    products.forEach((product) => {
      const category = product.categoryName ?? product.category_name ?? product.category?.name ?? t('adminDashboard.uncategorized');
      productsByCategory.set(category, (productsByCategory.get(category) ?? 0) + 1);
    });

    return {
      customers,
      totalRevenue,
      pendingOrders,
      lowStockProducts,
      monthlyData: [...monthly.values()].sort((a, b) => a.month.localeCompare(b.month)).slice(-8),
      ordersByStatus: [...statuses.entries()].map(([name, value]) => ({ name, value })),
      topSellingProducts: [...topProducts.values()].sort((a, b) => b.quantity - a.quantity).slice(0, 6),
      productsByCategory: [...productsByCategory.entries()].map(([name, value]) => ({ name, value })).slice(0, 8),
      customerSegments: [
        { name: t('adminDashboard.segments.customers'), value: customers.length },
        { name: t('adminDashboard.segments.admins'), value: users.filter((user) => user.role === 'admin').length },
      ],
    };
  }, [orders, products, t, users]);

  const statCards = [
    { label: t('adminDashboard.stats.totalUsers'), value: users.length, icon: <Users size={20} />, tone: '#0f766e' },
    { label: t('adminDashboard.stats.totalCustomers'), value: analytics.customers.length, icon: <Users size={20} />, tone: '#14b8a6' },
    { label: t('adminDashboard.stats.totalProducts'), value: products.length, icon: <Boxes size={20} />, tone: '#6366f1' },
    { label: t('adminDashboard.stats.totalOrders'), value: orders.length, icon: <ShoppingCart size={20} />, tone: '#f59e0b' },
    { label: t('adminDashboard.stats.totalRevenue'), value: formatPrice(analytics.totalRevenue), icon: <WalletCards size={20} />, tone: '#16a34a' },
    { label: t('adminDashboard.stats.pendingOrders'), value: analytics.pendingOrders, icon: <AlertCircle size={20} />, tone: '#f59e0b' },
    { label: t('adminDashboard.stats.lowStock'), value: analytics.lowStockProducts.length, icon: <Boxes size={20} />, tone: '#ef4444' },
    { label: t('adminDashboard.stats.totalReviews'), value: reviews.length, icon: <Star size={20} />, tone: '#8b5cf6' },
  ];

  const productsByCategoryTotal = analytics.productsByCategory.reduce((sum, item) => sum + Number(item.value ?? 0), 0);

  const navItems = [
    { id: 'overview' as const, label: t('adminDashboard.nav.overview'), icon: <LayoutDashboard size={18} /> },
    { id: 'orders' as const, label: t('adminDashboard.nav.orders'), icon: <ShoppingCart size={18} /> },
    { id: 'products' as const, label: t('adminDashboard.nav.products'), icon: <Boxes size={18} /> },
    { id: 'users' as const, label: t('adminDashboard.nav.users'), icon: <Users size={18} /> },
    { id: 'insights' as const, label: t('adminDashboard.nav.insights'), icon: <BarChart3 size={18} /> },
  ];

  if (hasError) {
    return (
      <div className="container" style={{ padding: '2rem 1rem 4rem' }}>
        <ErrorState
          title={t('adminDashboard.errors.title')}
          message={t('adminDashboard.errors.message')}
          onRetry={() => {
            void productsQuery.refetch();
            void categoriesQuery.refetch();
            void ordersQuery.refetch();
            void usersQuery.refetch();
            void reviewsQuery.refetch();
          }}
        />
      </div>
    );
  }

  return (
    <div style={{ background: 'rgb(var(--muted) / 0.28)', minHeight: 'calc(100vh - 80px)' }}>
      <div className="container" style={{ padding: '1.5rem 1rem 4rem' }}>
        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(180px, 240px) minmax(0, 1fr)',
            gap: '1.25rem',
            alignItems: 'start',
          }}
        >
          <aside
            style={{
              position: 'sticky',
              top: '1rem',
              background: 'rgb(var(--card))',
              border: '1px solid rgb(var(--border))',
              borderRadius: 'var(--radius)',
              padding: '1rem',
              boxShadow: '0 10px 30px rgba(15,23,42,0.05)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem' }}>
              <div style={{ width: 42, height: 42, borderRadius: 12, background: 'rgb(var(--primary))', color: 'white', display: 'grid', placeItems: 'center' }}>
                <LayoutDashboard size={22} />
              </div>
              <div>
                <strong>{t('adminDashboard.title')}</strong>
                <p style={{ fontSize: '0.78rem', color: 'rgb(var(--muted-foreground))' }}>{t('adminDashboard.subtitle')}</p>
              </div>
            </div>
            <nav style={{ display: 'grid', gap: '0.35rem' }}>
              {navItems.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setActiveTab(item.id)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.65rem',
                    padding: '0.7rem 0.75rem',
                    borderRadius: 'var(--radius)',
                    background: activeTab === item.id ? 'rgb(var(--primary) / 0.12)' : 'transparent',
                    color: activeTab === item.id ? 'rgb(var(--primary))' : 'rgb(var(--foreground))',
                    fontWeight: activeTab === item.id ? 800 : 600,
                    cursor: 'pointer',
                  }}
                >
                  {item.icon}
                  {item.label}
                </button>
              ))}
            </nav>
          </aside>

          <main style={{ display: 'grid', gap: '1.25rem', minWidth: 0 }}>
            <section
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                gap: '1rem',
                alignItems: 'center',
                flexWrap: 'wrap',
              }}
            >
              <div>
                <h1 style={{ fontSize: 'clamp(1.6rem, 2vw, 2.1rem)', fontWeight: 900 }}>{t('adminDashboard.heading')}</h1>
                <p style={{ color: 'rgb(var(--muted-foreground))', marginTop: 4 }}>{t('adminDashboard.description')}</p>
              </div>
              <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                <Button variant="primary" onClick={() => setActiveTab('products')}><PackagePlus size={16} /> {t('adminDashboard.actions.addProduct')}</Button>
                <Button variant="outline" onClick={() => setActiveTab('insights')}><BrainCircuit size={16} /> {t('adminDashboard.actions.viewAi')}</Button>
              </div>
            </section>

            {isLoading ? (
              <div style={{ display: 'grid', gap: '1rem' }}>
                <div className="grid grid-cols-4">
                  {Array.from({ length: 8 }).map((_, index) => <Skeleton key={index} height={120} />)}
                </div>
                <Skeleton height={320} />
              </div>
            ) : (
              <>
                <section className="admin-stats-grid">
                  {statCards.map((card) => (
                    <Card key={card.label} className="admin-stat-card">
                      <CardBody>
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '1rem', alignItems: 'flex-start' }}>
                          <div>
                            <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.78rem', fontWeight: 700 }}>{card.label}</p>
                            <strong style={{ display: 'block', marginTop: 8, fontSize: '1.55rem', fontWeight: 900 }}>{card.value}</strong>
                          </div>
                          <span style={{ width: 42, height: 42, borderRadius: 13, display: 'grid', placeItems: 'center', color: card.tone, background: `${card.tone}18` }}>
                            {card.icon}
                          </span>
                        </div>
                      </CardBody>
                    </Card>
                  ))}
                </section>

                {activeTab === 'overview' && (
                  <>
                    <section className="admin-chart-grid admin-chart-grid-overview">
                      <ChartCard title={t('adminDashboard.charts.salesByMonth')}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={analytics.monthlyData} margin={{ top: 16, right: 18, left: 0, bottom: 10 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgb(var(--border))" />
                            <XAxis dataKey="month" tick={CHART_AXIS_STYLE} axisLine={false} tickLine={false} minTickGap={14} />
                            <YAxis tick={CHART_AXIS_STYLE} axisLine={false} tickLine={false} width={42} />
                            <Tooltip cursor={{ fill: 'rgb(var(--muted) / 0.38)' }} contentStyle={CHART_TOOLTIP_STYLE} />
                            <Legend wrapperStyle={CHART_LEGEND_STYLE} />
                            <Bar dataKey="sales" name={t('adminDashboard.chartKeys.sales')} fill="#0f766e" radius={[8, 8, 0, 0]} barSize={34} />
                          </BarChart>
                        </ResponsiveContainer>
                      </ChartCard>
                      <ChartCard title={t('adminDashboard.charts.ordersByStatus')}>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart margin={{ top: 12, right: 12, left: 12, bottom: 12 }}>
                            <Pie data={analytics.ordersByStatus} dataKey="value" nameKey="name" innerRadius={46} outerRadius={82} paddingAngle={3} labelLine={false} label={({ percent }: any) => `${Math.round((percent ?? 0) * 100)}%`}>
                              {analytics.ordersByStatus.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                            </Pie>
                            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
                            <Legend verticalAlign="bottom" iconType="circle" wrapperStyle={CHART_LEGEND_STYLE} />
                          </PieChart>
                        </ResponsiveContainer>
                      </ChartCard>
                    </section>

                    <section style={{ display: 'grid', gridTemplateColumns: 'repeat(3, minmax(0, 1fr))', gap: '1rem' }}>
                      <QuickAction icon={<PackagePlus size={18} />} label={t('adminDashboard.actions.addProduct')} onClick={() => setActiveTab('products')} />
                      <QuickAction icon={<FolderTree size={18} />} label={t('adminDashboard.actions.manageCategories')} onClick={() => setActiveTab('products')} />
                      <QuickAction icon={<Users size={18} />} label={t('adminDashboard.actions.manageUsers')} onClick={() => setActiveTab('users')} />
                      <QuickAction icon={<ShoppingCart size={18} />} label={t('adminDashboard.actions.viewOrders')} onClick={() => setActiveTab('orders')} />
                      <QuickAction icon={<BrainCircuit size={18} />} label={t('adminDashboard.actions.viewAi')} onClick={() => setActiveTab('insights')} />
                      <QuickAction icon={<Tags size={18} />} label={t('adminDashboard.actions.manageCategories')} onClick={() => setActiveTab('products')} />
                    </section>

                    <section style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '1rem' }}>
                      <RecentOrdersTable orders={orders.slice(0, 6)} t={t} />
                      <LowStockTable products={analytics.lowStockProducts.slice(0, 6)} t={t} />
                    </section>
                  </>
                )}

                {activeTab === 'insights' && (
                  <>
                    <section className="admin-chart-grid">
                      <ChartCard title={t('adminDashboard.charts.revenueEvolution')}>
                        <ResponsiveContainer width="100%" height="100%">
                          <AreaChart data={analytics.monthlyData} margin={{ top: 16, right: 20, left: 0, bottom: 10 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgb(var(--border))" />
                            <XAxis dataKey="month" tick={CHART_AXIS_STYLE} axisLine={false} tickLine={false} minTickGap={14} />
                            <YAxis tick={CHART_AXIS_STYLE} axisLine={false} tickLine={false} width={54} tickFormatter={(value) => formatPrice(Number(value)).replace('.00', '')} />
                            <Tooltip formatter={(value) => formatPrice(Number(value))} contentStyle={CHART_TOOLTIP_STYLE} />
                            <Legend wrapperStyle={CHART_LEGEND_STYLE} />
                            <Area type="monotone" dataKey="revenue" name={t('adminDashboard.chartKeys.revenue')} stroke="#0f766e" fill="#14b8a650" />
                          </AreaChart>
                        </ResponsiveContainer>
                      </ChartCard>
                      <ChartCard title={t('adminDashboard.charts.topSellingProducts')}>
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={analytics.topSellingProducts} layout="vertical" margin={{ top: 12, right: 22, left: 16, bottom: 10 }}>
                            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="rgb(var(--border))" />
                            <XAxis type="number" tick={CHART_AXIS_STYLE} axisLine={false} tickLine={false} />
                            <YAxis type="category" dataKey="name" width={128} tick={CHART_AXIS_STYLE} axisLine={false} tickLine={false} tickFormatter={(value) => shortLabel(value, 18)} />
                            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
                            <Legend wrapperStyle={CHART_LEGEND_STYLE} />
                            <Bar dataKey="quantity" name={t('adminDashboard.chartKeys.quantity')} fill="#6366f1" radius={[0, 8, 8, 0]} barSize={20} />
                          </BarChart>
                        </ResponsiveContainer>
                      </ChartCard>
                      <ChartCard title={t('adminDashboard.charts.customersBySegment')}>
                        <ResponsiveContainer width="100%" height="100%">
                          <PieChart margin={{ top: 12, right: 12, left: 12, bottom: 12 }}>
                            <Pie data={analytics.customerSegments} dataKey="value" nameKey="name" innerRadius={48} outerRadius={84} paddingAngle={4} labelLine={false} label={({ percent }: any) => `${Math.round((percent ?? 0) * 100)}%`}>
                              {analytics.customerSegments.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                            </Pie>
                            <Tooltip contentStyle={CHART_TOOLTIP_STYLE} />
                            <Legend verticalAlign="bottom" iconType="circle" wrapperStyle={CHART_LEGEND_STYLE} />
                          </PieChart>
                        </ResponsiveContainer>
                      </ChartCard>
                      <ChartCard title={t('adminDashboard.charts.productsByCategory')} className="admin-category-chart-card">
                        <div className="admin-category-chart-layout">
                          <div className="admin-category-chart-visual">
                            {productsByCategoryTotal > 0 ? (
                              <ResponsiveContainer width="100%" height="100%">
                                <PieChart margin={{ top: 12, right: 12, bottom: 12, left: 12 }}>
                                  <Pie
                                    data={analytics.productsByCategory}
                                    dataKey="value"
                                    nameKey="name"
                                    innerRadius="56%"
                                    outerRadius="82%"
                                    paddingAngle={4}
                                    cornerRadius={8}
                                    stroke="rgb(var(--card))"
                                    strokeWidth={3}
                                  >
                                    {analytics.productsByCategory.map((_, index) => (
                                      <Cell key={index} fill={CATEGORY_COLORS[index % CATEGORY_COLORS.length]} />
                                    ))}
                                  </Pie>
                                  <Tooltip content={<CategoryTooltip total={productsByCategoryTotal} t={t} />} />
                                </PieChart>
                              </ResponsiveContainer>
                            ) : (
                              <div className="admin-category-empty">{t('common.noData')}</div>
                            )}
                            <div className="admin-category-center">
                              <strong>{productsByCategoryTotal}</strong>
                              <span>{t('adminDashboard.chartKeys.products')}</span>
                            </div>
                          </div>

                          <div className="admin-category-legend">
                            {analytics.productsByCategory.map((item, index) => {
                              const count = Number(item.value ?? 0);
                              const percent = productsByCategoryTotal > 0 ? Math.round((count / productsByCategoryTotal) * 100) : 0;

                              return (
                                <div className="admin-category-legend-item" key={item.name}>
                                  <span className="admin-category-dot" style={{ background: CATEGORY_COLORS[index % CATEGORY_COLORS.length] }} />
                                  <span className="admin-category-name" title={item.name}>{item.name}</span>
                                  <strong>{count}</strong>
                                  <em>{percent}%</em>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      </ChartCard>
                    </section>
                    <section className="admin-chart-grid admin-unavailable-grid">
                      <UnavailableCard title={t('adminDashboard.charts.aiPriceActivity')} message={t('adminDashboard.unavailable.aiPriceActivity')} icon={<BrainCircuit size={20} />} />
                      <UnavailableCard title={t('adminDashboard.charts.chatbotUsage')} message={t('adminDashboard.unavailable.chatbotUsage')} icon={<Bot size={20} />} />
                    </section>
                  </>
                )}

                {activeTab === 'orders' && <RecentOrdersTable orders={orders} t={t} />}
                {activeTab === 'products' && <ProductsTable products={products} categories={categories} t={t} />}
                {activeTab === 'users' && (
                  <section style={{ display: 'grid', gap: '1rem' }}>
                    <RecentUsersTable users={users} t={t} />
                    <LatestReviewsTable reviews={reviews.slice(0, 8)} t={t} />
                  </section>
                )}
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  );
};

const QuickAction: React.FC<{ icon: React.ReactNode; label: string; onClick: () => void }> = ({ icon, label, onClick }) => (
  <button
    type="button"
    onClick={onClick}
    style={{
      display: 'flex',
      alignItems: 'center',
      gap: '0.75rem',
      padding: '1rem',
      border: '1px solid rgb(var(--border))',
      borderRadius: 'var(--radius)',
      background: 'rgb(var(--card))',
      boxShadow: '0 10px 24px rgba(15,23,42,0.04)',
      cursor: 'pointer',
      fontWeight: 800,
    }}
  >
    <span style={{ width: 38, height: 38, borderRadius: 12, display: 'grid', placeItems: 'center', color: 'rgb(var(--primary))', background: 'rgb(var(--primary) / 0.12)' }}>{icon}</span>
    {label}
  </button>
);

function RecentOrdersTable({ orders, t }: { orders: any[]; t: any }) {
  if (!orders.length) return <EmptyState title={t('adminDashboard.empty.ordersTitle')} message={t('adminDashboard.empty.ordersMessage')} />;
  return (
    <Card>
      <CardHeader><CardTitle>{t('adminDashboard.tables.recentOrders')}</CardTitle></CardHeader>
      <CardBody>
        <TableContainer>
          <Table>
            <TableHeader><TableRow><TableHead>{t('adminDashboard.columns.order')}</TableHead><TableHead>{t('adminDashboard.columns.customer')}</TableHead><TableHead>{t('adminDashboard.columns.status')}</TableHead><TableHead>{t('adminDashboard.columns.total')}</TableHead><TableHead>{t('adminDashboard.columns.date')}</TableHead></TableRow></TableHeader>
            <TableBody>
              {orders.map((order) => (
                <TableRow key={order.id}>
                  <TableCell>#{order.id}</TableCell>
                  <TableCell>{[order.firstName ?? order.first_name, order.lastName ?? order.last_name].filter(Boolean).join(' ') || order.email || '-'}</TableCell>
                  <TableCell><Badge variant={statusVariant(String(order.status)) as any}>{t(`adminDashboard.status.${order.status}`, order.status)}</Badge></TableCell>
                  <TableCell>{formatPrice(getOrderTotal(order))}</TableCell>
                  <TableCell>{formatDate(order.createdAt ?? order.created_at)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardBody>
    </Card>
  );
}

function RecentUsersTable({ users, t }: { users: any[]; t: any }) {
  if (!users.length) return <EmptyState title={t('adminDashboard.empty.usersTitle')} message={t('adminDashboard.empty.usersMessage')} />;
  return (
    <Card>
      <CardHeader><CardTitle>{t('adminDashboard.tables.recentUsers')}</CardTitle></CardHeader>
      <CardBody>
        <TableContainer>
          <Table>
            <TableHeader><TableRow><TableHead>{t('adminDashboard.columns.user')}</TableHead><TableHead>{t('adminDashboard.columns.email')}</TableHead><TableHead>{t('adminDashboard.columns.role')}</TableHead><TableHead>{t('adminDashboard.columns.status')}</TableHead></TableRow></TableHeader>
            <TableBody>
              {users.slice(0, 8).map((user) => (
                <TableRow key={user.id}>
                  <TableCell>{[user.firstName, user.lastName].filter(Boolean).join(' ') || `#${user.id}`}</TableCell>
                  <TableCell>{user.email}</TableCell>
                  <TableCell>{t(`adminDashboard.roles.${user.role}`, user.role)}</TableCell>
                  <TableCell><Badge variant={user.isActive === false ? 'danger' : 'success'}>{user.isActive === false ? t('adminDashboard.status.inactive') : t('adminDashboard.status.active')}</Badge></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardBody>
    </Card>
  );
}

function LowStockTable({ products, t }: { products: any[]; t: any }) {
  if (!products.length) return <EmptyState title={t('adminDashboard.empty.lowStockTitle')} message={t('adminDashboard.empty.lowStockMessage')} />;
  return (
    <Card>
      <CardHeader><CardTitle>{t('adminDashboard.tables.lowStockProducts')}</CardTitle></CardHeader>
      <CardBody>
        <TableContainer>
          <Table>
            <TableHeader><TableRow><TableHead>{t('adminDashboard.columns.product')}</TableHead><TableHead>{t('adminDashboard.columns.category')}</TableHead><TableHead>{t('adminDashboard.columns.stock')}</TableHead></TableRow></TableHeader>
            <TableBody>
              {products.map((product) => (
                <TableRow key={product.id}>
                  <TableCell>{product.name}</TableCell>
                  <TableCell>{product.categoryName ?? product.category_name ?? '-'}</TableCell>
                  <TableCell><Badge variant="warning">{product.stock}</Badge></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardBody>
    </Card>
  );
}

function ProductsTable({ products, categories, t }: { products: any[]; categories: any[]; t: any }) {
  if (!products.length) return <EmptyState title={t('adminDashboard.empty.productsTitle')} message={t('adminDashboard.empty.productsMessage')} />;
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t('adminDashboard.tables.products')}</CardTitle>
        <p style={{ color: 'rgb(var(--muted-foreground))', fontSize: '0.82rem' }}>{t('adminDashboard.tableNotes.products', { count: categories.length })}</p>
      </CardHeader>
      <CardBody>
        <TableContainer>
          <Table>
            <TableHeader><TableRow><TableHead>{t('adminDashboard.columns.product')}</TableHead><TableHead>{t('adminDashboard.columns.category')}</TableHead><TableHead>{t('adminDashboard.columns.price')}</TableHead><TableHead>{t('adminDashboard.columns.stock')}</TableHead><TableHead>{t('adminDashboard.columns.status')}</TableHead></TableRow></TableHeader>
            <TableBody>
              {products.slice(0, 20).map((product) => (
                <TableRow key={product.id}>
                  <TableCell>{product.name}</TableCell>
                  <TableCell>{product.categoryName ?? product.category_name ?? '-'}</TableCell>
                  <TableCell>{formatPrice(product.price)}</TableCell>
                  <TableCell>{product.stock}</TableCell>
                  <TableCell><Badge variant={product.is_active === false ? 'danger' : 'success'}>{product.is_active === false ? t('adminDashboard.status.inactive') : t('adminDashboard.status.active')}</Badge></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardBody>
    </Card>
  );
}

function LatestReviewsTable({ reviews, t }: { reviews: any[]; t: any }) {
  if (!reviews.length) return <EmptyState title={t('adminDashboard.empty.reviewsTitle')} message={t('adminDashboard.empty.reviewsMessage')} />;
  return (
    <Card>
      <CardHeader><CardTitle>{t('adminDashboard.tables.latestReviews')}</CardTitle></CardHeader>
      <CardBody>
        <TableContainer>
          <Table>
            <TableHeader><TableRow><TableHead>{t('adminDashboard.columns.product')}</TableHead><TableHead>{t('adminDashboard.columns.customer')}</TableHead><TableHead>{t('adminDashboard.columns.rating')}</TableHead><TableHead>{t('adminDashboard.columns.review')}</TableHead></TableRow></TableHeader>
            <TableBody>
              {reviews.map((review) => (
                <TableRow key={review.id}>
                  <TableCell>{review.product_title ?? `#${review.product_id}`}</TableCell>
                  <TableCell>{[review.first_name, review.last_name].filter(Boolean).join(' ') || review.email || '-'}</TableCell>
                  <TableCell>{review.rating}/5</TableCell>
                  <TableCell>{review.review_text ?? '-'}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </CardBody>
    </Card>
  );
}
