import {
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from 'chart.js';
import { Line } from 'react-chartjs-2';
import type { SeriesPoint } from '../lib/api';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, Filler);

interface TimeSeriesChartProps {
  points: SeriesPoint[];
}

export default function TimeSeriesChart({ points }: TimeSeriesChartProps) {
  const data = {
    labels: points.map((p) => p.label),
    datasets: [
      {
        label: 'NDVI',
        data: points.map((p) => p.ndvi),
        borderColor: '#0f8f83',
        backgroundColor: 'rgba(15, 143, 131, 0.15)',
        fill: true,
        tension: 0.3,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    scales: { y: { min: 0, max: 1 } },
  };

  return (
    <div className="h-80 w-full rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <Line data={data} options={options} />
    </div>
  );
}
