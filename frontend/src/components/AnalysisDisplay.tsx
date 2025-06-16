/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React from 'react';
import ChartDisplay from './ChartDisplay';

interface AnalysisDisplayProps {
  analysisData: any;
}

interface InventoryAnalysisData {
  analysis_type: string;
  summary: {
    total_items: number;
    critical_items_count: number;
    low_stock_items_count: number;
    recommendations_count: number;
    charts_generated: number;
    ai_interactions: number;
    tools_used: string[];
  };
  recommendations: string[];
  visualizations?: any[];
  ai_analysis?: {
    inventory_insights?: {
      inventory_health_score?: number;
      high_turnover_products?: string[];
      low_turnover_products?: string[];
    };
    smart_alerts?: Array<{
      priority: string;
      type: string;
      message: string;
      recommended_action: string;
    }>;
    strategic_recommendations?: string[];
    inventory_kpis?: Record<string, number>;
  };
  demand_predictions?: Array<{
    product_id: number;
    predicted_demand_30d: number;
    predicted_demand_60d: number;
    predicted_demand_90d: number;
    confidence_score: number;
    trend: string;
    risk_level: string;
  }>;
}

const AnalysisDisplay: React.FC<AnalysisDisplayProps> = ({ analysisData }) => {
  const data = analysisData as InventoryAnalysisData;

  if (!data) {
    return (
      <div className='p-6 bg-gray-50 rounded-lg'>
        <div className='text-center text-gray-500'>
          <div className='text-lg font-medium'>
            No hay datos de análisis disponibles
          </div>
        </div>
      </div>
    );
  }

  // Only show inventory analysis card for actual inventory analysis
  const isInventoryAnalysis =
    data.analysis_type === 'enhanced_inventory_analysis' ||
    (data.summary && typeof data.summary.total_items === 'number');

  if (!isInventoryAnalysis) {
    // Return null for non-inventory analysis data to avoid showing the card
    return null;
  }

  const renderAnalysisSummary = () => (
    <div className='bg-gradient-to-r from-blue-50 to-indigo-100 p-6 rounded-xl border border-blue-200 mb-8'>
      <div className='flex items-center mb-4'>
        <span className='text-3xl mr-3'>📦</span>
        <div>
          <h2 className='text-2xl font-bold text-gray-900'>
            Análisis de Inventario Completado
          </h2>
          <p className='text-blue-700 font-medium'>
            Análisis inteligente con IA • {data.summary?.ai_interactions || 0}{' '}
            interacciones de IA
          </p>
        </div>
      </div>

      <div className='grid grid-cols-2 md:grid-cols-4 gap-4 mb-6'>
        <div className='bg-white p-4 rounded-lg shadow-sm border border-blue-100'>
          <div className='text-2xl font-bold text-blue-600'>
            {data.summary?.total_items || 0}
          </div>
          <div className='text-sm text-gray-600'>Total de productos</div>
        </div>
        <div className='bg-white p-4 rounded-lg shadow-sm border border-red-100'>
          <div className='text-2xl font-bold text-red-600'>
            {data.summary?.critical_items_count || 0}
          </div>
          <div className='text-sm text-gray-600'>Productos críticos</div>
        </div>
        <div className='bg-white p-4 rounded-lg shadow-sm border border-yellow-100'>
          <div className='text-2xl font-bold text-yellow-600'>
            {data.summary?.low_stock_items_count || 0}
          </div>
          <div className='text-sm text-gray-600'>Stock bajo</div>
        </div>
        <div className='bg-white p-4 rounded-lg shadow-sm border border-green-100'>
          <div className='text-2xl font-bold text-green-600'>
            {data.summary?.recommendations_count || 0}
          </div>
          <div className='text-sm text-gray-600'>Recomendaciones</div>
        </div>
      </div>

      {data.ai_analysis?.inventory_insights?.inventory_health_score && (
        <div className='bg-white p-4 rounded-lg border border-blue-100 mb-4'>
          <div className='flex items-center justify-between'>
            <div className='flex items-center'>
              <span className='text-2xl mr-3'>🏥</span>
              <div>
                <div className='font-semibold text-gray-900'>
                  Salud del Inventario
                </div>
                <div className='text-sm text-gray-600'>
                  Puntuación general del sistema
                </div>
              </div>
            </div>
            <div className='text-3xl font-bold text-blue-600'>
              {data.ai_analysis.inventory_insights.inventory_health_score.toFixed(
                1
              )}
              /10
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderSmartAlerts = () => {
    const alerts = data.ai_analysis?.smart_alerts;
    if (!alerts || alerts.length === 0) return null;

    return (
      <div className='mb-8'>
        <h3 className='text-xl font-bold text-gray-900 mb-4 flex items-center'>
          <span className='mr-2'>🚨</span>
          Alertas Inteligentes
        </h3>
        <div className='space-y-3'>
          {alerts.map((alert, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border-l-4 ${
                alert.priority === 'high'
                  ? 'bg-red-50 border-red-400'
                  : alert.priority === 'medium'
                  ? 'bg-yellow-50 border-yellow-400'
                  : 'bg-blue-50 border-blue-400'
              }`}
            >
              <div className='flex items-start justify-between'>
                <div className='flex-1'>
                  <div className='flex items-center mb-2'>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        alert.priority === 'high'
                          ? 'bg-red-100 text-red-800'
                          : alert.priority === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-blue-100 text-blue-800'
                      }`}
                    >
                      {alert.priority.toUpperCase()}
                    </span>
                    <span className='ml-2 text-sm text-gray-600 font-medium'>
                      {alert.type.replace(/_/g, ' ').toUpperCase()}
                    </span>
                  </div>
                  <div className='text-gray-900 font-medium mb-1'>
                    {alert.message}
                  </div>
                  <div className='text-sm text-gray-600'>
                    {alert.recommended_action}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderStrategicRecommendations = () => {
    const recommendations =
      data.ai_analysis?.strategic_recommendations || data.recommendations;
    if (!recommendations || recommendations.length === 0) return null;

    return (
      <div className='mb-8'>
        <h3 className='text-xl font-bold text-gray-900 mb-4 flex items-center'>
          <span className='mr-2'>💡</span>
          Recomendaciones Estratégicas
        </h3>
        <div className='bg-gradient-to-r from-green-50 to-emerald-50 p-6 rounded-lg border border-green-200'>
          <ul className='space-y-3'>
            {recommendations.map((recommendation: string, index: number) => (
              <li key={index} className='flex items-start'>
                <span className='text-green-500 mr-3 mt-1'>✓</span>
                <span className='text-gray-800'>{recommendation}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>
    );
  };

  const renderDemandPredictions = () => {
    const predictions = data.demand_predictions;
    if (!predictions || predictions.length === 0) return null;

    return (
      <div className='mb-8'>
        <h3 className='text-xl font-bold text-gray-900 mb-4 flex items-center'>
          <span className='mr-2'>🔮</span>
          Predicciones de Demanda
        </h3>
        <div className='bg-gradient-to-r from-purple-50 to-pink-50 p-6 rounded-lg border border-purple-200'>
          <div className='grid gap-4'>
            {predictions.slice(0, 5).map((prediction, index) => (
              <div
                key={index}
                className='bg-white p-4 rounded-lg border border-purple-100'
              >
                <div className='flex items-center justify-between mb-3'>
                  <div className='font-semibold text-gray-900'>
                    Producto {prediction.product_id}
                  </div>
                  <div className='flex items-center space-x-2'>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        prediction.confidence_score >= 0.8
                          ? 'bg-green-100 text-green-800'
                          : prediction.confidence_score >= 0.6
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {(prediction.confidence_score * 100).toFixed(0)}%
                      confianza
                    </span>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-semibold ${
                        prediction.risk_level === 'high'
                          ? 'bg-red-100 text-red-800'
                          : prediction.risk_level === 'medium'
                          ? 'bg-yellow-100 text-yellow-800'
                          : 'bg-green-100 text-green-800'
                      }`}
                    >
                      Riesgo {prediction.risk_level}
                    </span>
                  </div>
                </div>
                <div className='grid grid-cols-3 gap-3 text-sm'>
                  <div className='text-center p-2 bg-blue-50 rounded border border-blue-100'>
                    <div className='font-bold text-blue-600'>
                      {prediction.predicted_demand_30d}
                    </div>
                    <div className='text-blue-700'>30 días</div>
                  </div>
                  <div className='text-center p-2 bg-indigo-50 rounded border border-indigo-100'>
                    <div className='font-bold text-indigo-600'>
                      {prediction.predicted_demand_60d}
                    </div>
                    <div className='text-indigo-700'>60 días</div>
                  </div>
                  <div className='text-center p-2 bg-purple-50 rounded border border-purple-100'>
                    <div className='font-bold text-purple-600'>
                      {prediction.predicted_demand_90d}
                    </div>
                    <div className='text-purple-700'>90 días</div>
                  </div>
                </div>
                <div className='mt-2 text-xs text-gray-600'>
                  Tendencia:{' '}
                  <span className='font-medium'>{prediction.trend}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  };

  const renderKPIs = () => {
    const kpis = data.ai_analysis?.inventory_kpis;
    if (!kpis || Object.keys(kpis).length === 0) return null;

    return (
      <div className='mb-8'>
        <h3 className='text-xl font-bold text-gray-900 mb-4 flex items-center'>
          <span className='mr-2'>📊</span>
          Indicadores Clave de Rendimiento
        </h3>
        <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
          {Object.entries(kpis).map(([key, value]) => (
            <div
              key={key}
              className='bg-white p-4 rounded-lg shadow-sm border border-gray-200'
            >
              <div className='text-2xl font-bold text-indigo-600'>
                {typeof value === 'number' ? value.toFixed(2) : value}
              </div>
              <div className='text-sm text-gray-600 capitalize'>
                {key.replace(/_/g, ' ')}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className='space-y-6'>
      {renderAnalysisSummary()}
      {renderSmartAlerts()}
      {renderDemandPredictions()}
      {renderKPIs()}
      {renderStrategicRecommendations()}

      {/* Advanced Visualizations */}
      {data.visualizations && data.visualizations.length > 0 && (
        <ChartDisplay visualizations={data.visualizations} />
      )}
    </div>
  );
};

export default AnalysisDisplay;
