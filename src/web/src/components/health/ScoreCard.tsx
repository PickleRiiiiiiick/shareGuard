import { useState, useEffect } from 'react';
import { HEALTH_SCORE_THRESHOLDS, ISSUE_TYPE_LABELS } from '../../types/health';
import type { HealthScore } from '../../types/health';

interface ScoreCardProps {
    data: HealthScore;
}

export function ScoreCard({ data }: ScoreCardProps) {
    const [animatedScore, setAnimatedScore] = useState(0);
    const [isAnimating, setIsAnimating] = useState(true);
    
    // Validate data structure
    if (!data || !data.issueCountBySeverity || !data.issueCountByType) {
        return (
            <div className="bg-white rounded-lg shadow p-6">
                <div className="text-center text-gray-500">
                    <p>No health data available</p>
                    <p className="text-sm mt-2">Run a health scan to generate data</p>
                </div>
            </div>
        );
    }
    
    useEffect(() => {
        const duration = 2000; // 2 seconds
        const steps = 60;
        const increment = data.score / steps;
        let currentStep = 0;
        
        const timer = setInterval(() => {
            currentStep++;
            const currentScore = Math.min(Math.round(increment * currentStep), data.score);
            setAnimatedScore(currentScore);
            
            if (currentStep >= steps || currentScore >= data.score) {
                clearInterval(timer);
                setAnimatedScore(data.score);
                setIsAnimating(false);
            }
        }, duration / steps);
        
        return () => clearInterval(timer);
    }, [data.score]);

    const getScoreColor = (score: number) => {
        if (score > HEALTH_SCORE_THRESHOLDS.good) return 'text-green-600';
        if (score > HEALTH_SCORE_THRESHOLDS.warning) return 'text-yellow-600';
        return 'text-red-600';
    };

    const getScoreStrokeColor = (score: number) => {
        if (score > HEALTH_SCORE_THRESHOLDS.good) return 'stroke-green-600';
        if (score > HEALTH_SCORE_THRESHOLDS.warning) return 'stroke-yellow-600';
        return 'stroke-red-600';
    };

    const circumference = 2 * Math.PI * 60;
    const strokeDashoffset = circumference - (animatedScore / 100) * circumference;

    return (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="flex flex-col items-center justify-center">
                        <div className="relative">
                            <svg className="w-48 h-48 transform -rotate-90">
                                <circle
                                    cx="96"
                                    cy="96"
                                    r="70"
                                    stroke="currentColor"
                                    strokeWidth="8"
                                    fill="none"
                                    className="text-gray-200"
                                />
                                <circle
                                    cx="96"
                                    cy="96"
                                    r="70"
                                    strokeWidth="8"
                                    fill="none"
                                    className={getScoreStrokeColor(data.score)}
                                    strokeDasharray={circumference * 1.17}
                                    strokeDashoffset={strokeDashoffset * 1.17}
                                    strokeLinecap="round"
                                    style={{
                                        transition: 'stroke-dashoffset 0.1s ease-out'
                                    }}
                                />
                            </svg>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <div className="text-center">
                                    <div className={`text-4xl font-bold ${getScoreColor(data.score)}`}>
                                        {animatedScore}
                                        {isAnimating && (
                                            <span className="inline-block w-1 h-6 bg-current ml-1 animate-pulse"></span>
                                        )}
                                    </div>
                                    <div className="text-sm text-gray-500 font-medium mt-1">Health Score</div>
                                    {isAnimating && (
                                        <div className="mt-2">
                                            <div className="w-6 h-6 mx-auto border-2 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                        <div className="mt-4 text-sm text-gray-500">
                            Last scan: {new Date(data.lastScanTimestamp).toLocaleString()}
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h3 className="text-sm font-medium text-gray-900">Issues by Severity</h3>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-center space-x-2">
                                    <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                                    <span className="text-sm text-gray-700">Critical</span>
                                </div>
                                <span className="text-sm font-semibold text-red-600">
                                    {data.issueCountBySeverity.critical || 0}
                                </span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-center space-x-2">
                                    <div className="w-3 h-3 bg-orange-500 rounded-full"></div>
                                    <span className="text-sm text-gray-700">High</span>
                                </div>
                                <span className="text-sm font-semibold text-orange-600">
                                    {data.issueCountBySeverity.high || 0}
                                </span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-center space-x-2">
                                    <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                                    <span className="text-sm text-gray-700">Medium</span>
                                </div>
                                <span className="text-sm font-semibold text-yellow-600">
                                    {data.issueCountBySeverity.medium || 0}
                                </span>
                            </div>
                            <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                <div className="flex items-center space-x-2">
                                    <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
                                    <span className="text-sm text-gray-700">Low</span>
                                </div>
                                <span className="text-sm font-semibold text-blue-600">
                                    {data.issueCountBySeverity.low || 0}
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="space-y-4">
                        <h3 className="text-sm font-medium text-gray-900">Issues by Type</h3>
                        <div className="space-y-3">
                            {Object.entries(data.issueCountByType).map(([type, count]) => (
                                <div key={type} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                                    <span className="text-sm text-gray-700">
                                        {ISSUE_TYPE_LABELS[type as keyof typeof ISSUE_TYPE_LABELS]}
                                    </span>
                                    <span className="text-sm font-semibold text-gray-900">{count}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}