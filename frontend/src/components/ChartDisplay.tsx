'use client';

import React from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts';

interface ChartDataItem {
  [key: string]: string | number | undefined;
  name?: string;
  value?: number;
  color?: string;
}

interface Visualization {
  type: string;
  title: string;
  description?: string;
  data: ChartDataItem[];
  summary?: Record<string, string | number>;
  chart_id?: string;
  priority?: number;
}

interface ChartDisplayProps {
  visualizations: Visualization[];
  className?: string;
}

// Advanced color palette for charts
const CHART_COLORS = {
  primary: ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#F97316'],
  status: {
    Excelente: '#22c55e',
    Bueno: '#84cc16',
    Regular: '#eab308',
    Crítico: '#ef4444',
    Adecuado: '#22c55e',
    Bajo: '#eab308',
    Agotado: '#ef4444',
  },
  gradient: {
    blue: ['#3B82F6', '#1D4ED8'],
    green: ['#10B981', '#059669'],
    red: ['#EF4444', '#DC2626'],
    orange: ['#F59E0B', '#D97706'],
  },
};

const ChartDisplay: React.FC<ChartDisplayProps> = ({
  visualizations,
  className = '',
}) => {
  const sortedVisualizations = visualizations.sort(
    (a, b) => (a.priority || 10) - (b.priority || 10)
  );

  const renderChart = (visualization: Visualization) => {
    const { type, data } = visualization;

    if (!data || data.length === 0) {
      return (
        <div className='flex items-center justify-center h-64 bg-white/5 rounded-lg border-2 border-dashed border-white/20'>
          <div className='text-center text-white/60'>
            <div className='text-lg font-medium'>No hay datos disponibles</div>
            <div className='text-sm'>No se pudo generar la visualización</div>
          </div>
        </div>
      );
    }

    const containerHeight = type === 'pie' ? 400 : 350;

    switch (type.toLowerCase()) {
      case 'line':
        return (
          <ResponsiveContainer width='100%' height={containerHeight}>
            <LineChart
              data={data}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <defs>
                <linearGradient id='lineGradient' x1='0' y1='0' x2='0' y2='1'>
                  <stop offset='5%' stopColor='#3B82F6' stopOpacity={0.8} />
                  <stop offset='95%' stopColor='#3B82F6' stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray='3 3' stroke='#ffffff20' />
              <XAxis
                dataKey='name'
                stroke='#ffffff80'
                fontSize={12}
                angle={-45}
                textAnchor='end'
                height={80}
              />
              <YAxis stroke='#ffffff80' fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #ffffff20',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
                  color: '#ffffff',
                }}
              />
              <Legend />

              {/* Dynamic lines based on data keys */}
              {Object.keys(data[0] || {})
                .filter(
                  (key) => key !== 'name' && typeof data[0][key] === 'number'
                )
                .map((key, index) => (
                  <Line
                    key={key}
                    type='monotone'
                    dataKey={key}
                    stroke={
                      CHART_COLORS.primary[index % CHART_COLORS.primary.length]
                    }
                    strokeWidth={3}
                    dot={{
                      fill: CHART_COLORS.primary[
                        index % CHART_COLORS.primary.length
                      ],
                      strokeWidth: 2,
                      r: 4,
                    }}
                    activeDot={{
                      r: 6,
                      stroke:
                        CHART_COLORS.primary[
                          index % CHART_COLORS.primary.length
                        ],
                      strokeWidth: 2,
                    }}
                  />
                ))}
            </LineChart>
          </ResponsiveContainer>
        );

      case 'bar':
        return (
          <ResponsiveContainer width='100%' height={containerHeight}>
            <BarChart
              data={data}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <defs>
                {CHART_COLORS.primary.map((color, index) => (
                  <linearGradient
                    key={index}
                    id={`barGradient${index}`}
                    x1='0'
                    y1='0'
                    x2='0'
                    y2='1'
                  >
                    <stop offset='5%' stopColor={color} stopOpacity={0.9} />
                    <stop offset='95%' stopColor={color} stopOpacity={0.6} />
                  </linearGradient>
                ))}
              </defs>
              <CartesianGrid strokeDasharray='3 3' stroke='#ffffff20' />
              <XAxis
                dataKey='name'
                stroke='#ffffff80'
                fontSize={12}
                angle={-45}
                textAnchor='end'
                height={80}
              />
              <YAxis stroke='#ffffff80' fontSize={12} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #ffffff20',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
                  color: '#ffffff',
                }}
              />
              <Legend />

              {/* Dynamic bars with Spanish labels */}
              {Object.keys(data[0] || {})
                .filter(
                  (key) =>
                    key !== 'name' &&
                    key !== 'status' &&
                    key !== 'color' &&
                    key !== 'estado' &&
                    key !== 'ubicacion' &&
                    // Only show Spanish keys, filter out English duplicates
                    key !== 'quantity' &&
                    key !== 'min_threshold' &&
                    key !== 'max_threshold' &&
                    typeof data[0][key] === 'number'
                )
                .map((key, index) => {
                  // Translate English keys to Spanish
                  const keyMap: Record<string, string> = {
                    quantity: 'Cantidad',
                    min_threshold: 'Mínimo',
                    max_threshold: 'Máximo',
                    cantidad: 'Cantidad',
                    minimo: 'Mínimo',
                    maximo: 'Máximo',
                  };
                  const displayKey = keyMap[key] || key;

                  return (
                    <Bar
                      key={key}
                      dataKey={key}
                      name={displayKey}
                      fill={`url(#barGradient${
                        index % CHART_COLORS.primary.length
                      })`}
                      radius={[4, 4, 0, 0]}
                    />
                  );
                })}
            </BarChart>
          </ResponsiveContainer>
        );

      case 'pie':
        return (
          <ResponsiveContainer width='100%' height={containerHeight}>
            <PieChart>
              <Pie
                data={data}
                cx='50%'
                cy='50%'
                labelLine={false}
                label={false}
                outerRadius={100}
                innerRadius={40}
                fill='#8884d8'
                dataKey='value'
                stroke='#ffffff'
                strokeWidth={3}
              >
                {data.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={
                      (entry.color as string) ||
                      CHART_COLORS.status[
                        entry.name as keyof typeof CHART_COLORS.status
                      ] ||
                      CHART_COLORS.primary[index % CHART_COLORS.primary.length]
                    }
                  />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  backgroundColor: '#1e293b',
                  border: '1px solid #ffffff20',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)',
                  color: '#ffffff',
                }}
                formatter={(value, name) => [`${value} productos`, name]}
              />
              <Legend
                verticalAlign='bottom'
                height={60}
                wrapperStyle={{
                  paddingTop: '30px',
                  fontSize: '14px',
                }}
                formatter={(value, entry) => {
                  const entryValue = entry?.payload?.value || 0;
                  const total = data.reduce(
                    (sum, item) => sum + (item.value || 0),
                    0
                  );
                  const percentage =
                    total > 0 ? ((entryValue / total) * 100).toFixed(1) : '0.0';
                  return `${value}: ${entryValue} (${percentage}%)`;
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width='100%' height={containerHeight}>
            <AreaChart
              data={data}
              margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
            >
              <defs>
                <linearGradient id='areaGradient' x1='0' y1='0' x2='0' y2='1'>
                  <stop offset='5%' stopColor='#10B981' stopOpacity={0.8} />
                  <stop offset='95%' stopColor='#10B981' stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray='3 3' stroke='#ffffff20' />
              <XAxis dataKey='name' stroke='#ffffff80' fontSize={12} />
              <YAxis stroke='#ffffff80' fontSize={12} />
              <Tooltip />
              <Area
                type='monotone'
                dataKey='value'
                stroke='#10B981'
                fillOpacity={1}
                fill='url(#areaGradient)'
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      default:
        return (
          <div className='flex items-center justify-center h-64 bg-white/5 rounded-lg'>
            <div className='text-white/60 text-center'>
              <div className='text-lg font-medium'>
                Tipo de gráfico no soportado
              </div>
              <div className='text-sm'>Tipo: {type}</div>
            </div>
          </div>
        );
    }
  };

  const renderSummaryCard = (
    summary: Record<string, string | number>,
    title: string
  ) => {
    if (!summary) return null;

    return (
      <div className='bg-gradient-to-r from-purple-500/20 to-blue-500/20 p-4 rounded-lg border border-purple-400/30 backdrop-blur-sm'>
        <h4 className='font-semibold text-white mb-3 flex items-center'>
          <span className='mr-2'>📊</span>
          Resumen: {title}
        </h4>
        <div className='grid grid-cols-2 md:grid-cols-3 gap-3 text-sm'>
          {Object.entries(summary).map(([key, value]) => (
            <div
              key={key}
              className='bg-white/10 p-2 rounded border border-white/20 backdrop-blur-sm'
            >
              <div className='text-purple-300 font-medium text-xs uppercase tracking-wide'>
                {key.replace(/_/g, ' ')}
              </div>
              <div className='text-white font-bold'>
                {typeof value === 'number'
                  ? key.includes('percentage') || key.includes('score')
                    ? `${value.toFixed(1)}%`
                    : value.toLocaleString()
                  : String(value)}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  if (!visualizations || visualizations.length === 0) {
    return (
      <div
        className={`bg-white/5 p-8 rounded-lg border-2 border-dashed border-white/20 ${className}`}
      >
        <div className='text-center text-white/60'>
          <div className='text-xl font-medium mb-2'>
            📊 No hay gráficas disponibles
          </div>
          <div className='text-sm'>
            Los datos de análisis no generaron visualizaciones
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-8 ${className}`}>
      <div className='text-center mb-6'>
        <h2 className='text-2xl font-bold text-white mb-2'>
          📈 Análisis Avanzado de Inventario
        </h2>
        <p className='text-white/70'>
          Dashboard inteligente con {visualizations.length} visualizaciones
          generadas por IA
        </p>
      </div>

      {sortedVisualizations.map((visualization, index) => (
        <div
          key={index}
          className='relative bg-slate-900/90 backdrop-blur-xl p-6 rounded-xl shadow-lg border border-white/20 hover:shadow-xl transition-shadow duration-300'
        >
          <div className='absolute inset-0 rounded-xl bg-gradient-to-br from-slate-800/50 via-purple-900/30 to-slate-800/50 pointer-events-none' />
          <div className='relative z-10'>
            <div className='mb-6'>
              <div className='flex items-center justify-between mb-2'>
                <h3 className='text-xl font-bold text-white flex items-center'>
                  <span className='mr-2'>
                    {visualization.type === 'pie'
                      ? '🥧'
                      : visualization.type === 'line'
                      ? '📈'
                      : visualization.type === 'bar'
                      ? '📊'
                      : '📉'}
                  </span>
                  {visualization.title}
                </h3>
                {visualization.chart_id && (
                  <span className='text-xs bg-white/10 text-white/70 px-2 py-1 rounded-full border border-white/20'>
                    ID: {visualization.chart_id}
                  </span>
                )}
              </div>
              {visualization.description && (
                <p className='text-white/70 text-sm'>
                  {visualization.description}
                </p>
              )}
            </div>

            {renderChart(visualization)}

            {visualization.summary && (
              <div className='mt-6'>
                {renderSummaryCard(visualization.summary, visualization.title)}
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default ChartDisplay;
