import React, { useState, useEffect } from "react";
import "./Timeline.css";

interface Session {
  category: string;
  title: string;
  startTime: string;
  duration: number;
  confidence: "high" | "medium" | "low";
  filename: string;
  preview: string;
}

interface CategoryStats {
  duration: number;
  percentage: number;
  sessions: number;
  color: string;
}

interface TimelineData {
  sessions: Session[];
  totalDuration: number;
  categories: Record<string, CategoryStats>;
  metadata: {
    generated: string;
    totalSessions: number;
    timeRange: {
      start: string;
      end: string;
    };
  };
}

interface TimelineSegmentProps {
  session: Session;
  totalDuration: number;
  color: string;
}

const TimelineSegment: React.FC<TimelineSegmentProps> = ({
  session,
  totalDuration,
  color,
}: TimelineSegmentProps) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const widthPercent = (session.duration / totalDuration) * 100;

  const opacity = {
    high: 1,
    medium: 0.8,
    low: 0.6,
  }[session.confidence];

  return (
    <div
      className="timeline-segment"
      style={{
        width: `${widthPercent}%`,
        backgroundColor: color,
        opacity,
      }}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {showTooltip && (
        <div className="timeline-tooltip">
          <div className="tooltip-title">{session.title}</div>
          <div className="tooltip-info">
            <div>Category: {session.category}</div>
            <div>Duration: {session.duration} min</div>
            <div>Confidence: {session.confidence}</div>
            <div className="tooltip-preview">{session.preview}</div>
          </div>
        </div>
      )}
    </div>
  );
};

interface PieChartProps {
  categories: Record<string, CategoryStats>;
}

const PieChart: React.FC<PieChartProps> = ({ categories }: PieChartProps) => {
  const [hoveredSegment, setHoveredSegment] = useState<string | null>(null);

  const sortedCategories = Object.entries(categories)
    .filter(([_, stats]) => stats.sessions > 0)
    .sort(([_, a], [__, b]) => b.duration - a.duration);

  const radius = 120;
  const centerX = 150;
  const centerY = 150;
  const strokeWidth = 2;

  let cumulativePercentage = 0;

  const createPath = (startAngle: number, endAngle: number, radius: number) => {
    const x1 = centerX + radius * Math.cos(startAngle);
    const y1 = centerY + radius * Math.sin(startAngle);
    const x2 = centerX + radius * Math.cos(endAngle);
    const y2 = centerY + radius * Math.sin(endAngle);

    const largeArcFlag = endAngle - startAngle > Math.PI ? 1 : 0;

    return `M ${centerX} ${centerY} L ${x1} ${y1} A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2} Z`;
  };

  return (
    <div className="pie-chart-container">
      <h3>Time Distribution by Category</h3>
      <div className="pie-chart-wrapper">
        <svg width="300" height="300" className="pie-chart">
          {sortedCategories.map(([name, stats]) => {
            const startAngle =
              (cumulativePercentage / 100) * 2 * Math.PI - Math.PI / 2;
            const endAngle =
              ((cumulativePercentage + stats.percentage) / 100) * 2 * Math.PI -
              Math.PI / 2;
            const path = createPath(startAngle, endAngle, radius);

            cumulativePercentage += stats.percentage;

            const isHovered = hoveredSegment === name;
            const segmentRadius = isHovered ? radius + 5 : radius;
            const hoveredPath = isHovered
              ? createPath(startAngle, endAngle, segmentRadius)
              : path;

            return (
              <g key={name}>
                <path
                  d={hoveredPath}
                  fill={stats.color}
                  stroke="white"
                  strokeWidth={strokeWidth}
                  onMouseEnter={() => setHoveredSegment(name)}
                  onMouseLeave={() => setHoveredSegment(null)}
                  style={{
                    cursor: "pointer",
                    transition: "all 0.2s ease",
                    opacity:
                      hoveredSegment && hoveredSegment !== name ? 0.7 : 1,
                  }}
                />
                {/* Add percentage labels for larger segments */}
                {stats.percentage > 5 && (
                  <text
                    x={
                      centerX +
                      segmentRadius *
                        0.7 *
                        Math.cos((startAngle + endAngle) / 2)
                    }
                    y={
                      centerY +
                      segmentRadius *
                        0.7 *
                        Math.sin((startAngle + endAngle) / 2)
                    }
                    textAnchor="middle"
                    dominantBaseline="middle"
                    fill="white"
                    fontSize="12"
                    fontWeight="600"
                    style={{ pointerEvents: "none" }}
                  >
                    {Math.round(stats.percentage)}%
                  </text>
                )}
              </g>
            );
          })}
        </svg>

        {hoveredSegment && (
          <div className="pie-tooltip">
            <div className="pie-tooltip-content">
              <div className="pie-tooltip-category">{hoveredSegment}</div>
              <div className="pie-tooltip-stats">
                {categories[hoveredSegment].percentage.toFixed(1)}% •{" "}
                {categories[hoveredSegment].duration}min
              </div>
              <div className="pie-tooltip-sessions">
                {categories[hoveredSegment].sessions} sessions
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

interface CategoryLegendProps {
  categories: Record<string, CategoryStats>;
}

const CategoryLegend: React.FC<CategoryLegendProps> = ({
  categories,
}: CategoryLegendProps) => {
  const sortedCategories = Object.entries(categories)
    .filter(([_, stats]) => stats.sessions > 0)
    .sort(([a], [b]) => a.localeCompare(b));

  return (
    <div className="category-legend">
      <h3>Categories</h3>
      <div className="legend-items">
        {sortedCategories.map(([name, stats]) => (
          <div key={name} className="legend-item">
            <div
              className="legend-color"
              style={{ backgroundColor: stats.color }}
            />
            <div className="legend-info">
              <div className="legend-name">{name}</div>
              <div className="legend-stats">
                {stats.percentage}% • {stats.duration}min • {stats.sessions}{" "}
                sessions
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

interface TimelineStatsProps {
  data: TimelineData;
}

const TimelineStats: React.FC<TimelineStatsProps> = ({
  data,
}: TimelineStatsProps) => {
  const totalHours = Math.floor(data.totalDuration / 60);
  const totalMinutes = data.totalDuration % 60;

  return (
    <div className="timeline-stats">
      <div className="stat-item">
        <div className="stat-value">{data.metadata.totalSessions}</div>
        <div className="stat-label">Total Sessions</div>
      </div>
      <div className="stat-item">
        <div className="stat-value">
          {totalHours}h {totalMinutes}m
        </div>
        <div className="stat-label">Total Time</div>
      </div>
      <div className="stat-item">
        <div className="stat-value">
          {Math.round(data.totalDuration / data.metadata.totalSessions)}m
        </div>
        <div className="stat-label">Avg Session</div>
      </div>
    </div>
  );
};

export const Timeline: React.FC = () => {
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTimelineData = async () => {
      try {
        // In production, this would be a proper API call
        // For now, we'll fetch from the public directory
        const response = await fetch("/timeline-data.json");
        if (!response.ok) {
          throw new Error("Failed to load timeline data");
        }
        const data = await response.json();
        setTimelineData(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    loadTimelineData();
  }, []);

  if (loading) {
    return (
      <div className="timeline-container loading">Loading timeline data...</div>
    );
  }

  if (error || !timelineData) {
    return (
      <div className="timeline-container error">
        Error loading timeline: {error || "No data available"}
      </div>
    );
  }

  return (
    <div className="timeline-container">
      <h2>Development Timeline</h2>

      <TimelineStats data={timelineData} />

      <div className="charts-section">
        <div className="timeline-bar-container">
          <div className="timeline-bar">
            {timelineData.sessions.map((session, index) => (
              <TimelineSegment
                key={`${session.filename}-${index}`}
                session={session}
                totalDuration={timelineData.totalDuration}
                color={
                  timelineData.categories[session.category]?.color || "#999"
                }
              />
            ))}
          </div>
          <div className="timeline-labels">
            <div>Start</div>
            <div>End</div>
          </div>
        </div>

        <PieChart categories={timelineData.categories} />
      </div>

      <CategoryLegend categories={timelineData.categories} />
    </div>
  );
};
