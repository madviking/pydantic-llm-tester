"""
Performance tracking and analysis for prompts.
"""

import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .base import BasePromptProvider


class PerformanceTracker:
    """
    Tracks and analyzes prompt performance.
    
    This component is responsible for recording test results for prompt versions
    and generating performance reports and analyses.
    """
    
    def __init__(self, prompt_provider: Optional[BasePromptProvider] = None):
        """
        Initialize with an optional prompt provider.
        
        Args:
            prompt_provider: The prompt provider to use for storage
        """
        self.logger = logging.getLogger(__name__)
        self.prompt_provider = prompt_provider
    
    def record_test_results(
        self, 
        prompt_id: str, 
        version: str, 
        test_results: Dict[str, Any]
    ) -> bool:
        """
        Record test results for a prompt version.
        
        Args:
            prompt_id: Identifier for the prompt
            version: Version string
            test_results: Test results data
            
        Returns:
            Success status
        """
        if not self.prompt_provider:
            self.logger.warning("No prompt provider available for recording performance")
            return False
        
        try:
            # Extract performance data from test results
            performance_data = self._extract_performance_data(test_results)
            
            # Record the performance data
            return self.prompt_provider.record_performance(prompt_id, version, performance_data)
        
        except Exception as e:
            self.logger.error(f"Error recording performance for prompt '{prompt_id}': {e}")
            return False
    
    def analyze_performance_trends(self, prompt_id: str) -> Dict[str, Any]:
        """
        Analyze performance trends across versions.
        
        Args:
            prompt_id: Identifier for the prompt
            
        Returns:
            Analysis data
        """
        if not self.prompt_provider:
            self.logger.warning("No prompt provider available for performance analysis")
            return {}
        
        try:
            # Get performance history
            performance_history = self.prompt_provider.get_performance_history(prompt_id)
            
            if not performance_history:
                return {
                    'prompt_id': prompt_id,
                    'error': 'No performance data available'
                }
            
            # Sort by timestamp
            performance_history.sort(key=lambda x: x.get('timestamp', ''))
            
            # Extract metric values
            accuracy_trend = [entry.get('accuracy', 0) for entry in performance_history]
            token_trend = [entry.get('tokens', {}).get('total', 0) for entry in performance_history]
            cost_trend = [entry.get('cost', 0) for entry in performance_history]
            
            # Calculate trends
            accuracy_improvement = self._calculate_trend(accuracy_trend)
            token_efficiency = self._calculate_trend(token_trend, decreasing_is_good=True)
            cost_efficiency = self._calculate_trend(cost_trend, decreasing_is_good=True)
            
            # Find best and worst versions
            best_version = self.prompt_provider.get_best_performing_version(prompt_id, 'accuracy')
            best_accuracy = max(accuracy_trend) if accuracy_trend else 0
            
            # Create analysis
            analysis = {
                'prompt_id': prompt_id,
                'versions_count': len(performance_history),
                'latest_version': performance_history[-1].get('version') if performance_history else None,
                'first_version': performance_history[0].get('version') if performance_history else None,
                'best_version': best_version,
                'best_accuracy': best_accuracy,
                'trends': {
                    'accuracy': {
                        'values': accuracy_trend,
                        'improvement': accuracy_improvement,
                        'trend_direction': 'improving' if accuracy_improvement > 0 else 'declining' if accuracy_improvement < 0 else 'stable'
                    },
                    'tokens': {
                        'values': token_trend,
                        'improvement': token_efficiency,
                        'trend_direction': 'improving' if token_efficiency > 0 else 'declining' if token_efficiency < 0 else 'stable'
                    },
                    'cost': {
                        'values': cost_trend,
                        'improvement': cost_efficiency,
                        'trend_direction': 'improving' if cost_efficiency > 0 else 'declining' if cost_efficiency < 0 else 'stable'
                    }
                },
                'overall_assessment': self._generate_overall_assessment(accuracy_improvement, token_efficiency, cost_efficiency)
            }
            
            return analysis
        
        except Exception as e:
            self.logger.error(f"Error analyzing performance trends for '{prompt_id}': {e}")
            return {
                'prompt_id': prompt_id,
                'error': str(e)
            }
    
    def generate_performance_report(self, prompt_id: str) -> str:
        """
        Generate a detailed performance report.
        
        Args:
            prompt_id: Identifier for the prompt
            
        Returns:
            Markdown formatted report
        """
        if not self.prompt_provider:
            self.logger.warning("No prompt provider available for performance reporting")
            return "No prompt provider available"
        
        try:
            # Get analysis data
            analysis = self.analyze_performance_trends(prompt_id)
            
            if 'error' in analysis:
                return f"Error generating report: {analysis['error']}"
            
            # Get performance history
            performance_history = self.prompt_provider.get_performance_history(prompt_id)
            
            # Generate markdown report
            report = f"# Performance Report for Prompt: {prompt_id}\n\n"
            
            # Summary section
            report += "## Summary\n\n"
            report += f"- **Versions**: {analysis['versions_count']}\n"
            report += f"- **Best Version**: {analysis['best_version']} (Accuracy: {analysis['best_accuracy']:.2f}%)\n"
            report += f"- **Latest Version**: {analysis['latest_version']}\n"
            report += f"- **Overall Trend**: {analysis['overall_assessment']}\n\n"
            
            # Trends section
            report += "## Performance Trends\n\n"
            
            # Accuracy trend
            accuracy_trend = analysis['trends']['accuracy']
            report += "### Accuracy\n\n"
            report += f"- **Trend**: {accuracy_trend['trend_direction'].capitalize()}\n"
            report += f"- **Change**: {accuracy_trend['improvement']:.2f}%\n"
            report += "\n"
            
            # Token usage trend
            token_trend = analysis['trends']['tokens']
            report += "### Token Usage\n\n"
            report += f"- **Trend**: {token_trend['trend_direction'].capitalize()}\n"
            report += f"- **Change**: {token_trend['improvement']:.2f}%\n"
            report += "\n"
            
            # Cost trend
            cost_trend = analysis['trends']['cost']
            report += "### Cost\n\n"
            report += f"- **Trend**: {cost_trend['trend_direction'].capitalize()}\n"
            report += f"- **Change**: {cost_trend['improvement']:.2f}%\n"
            report += "\n"
            
            # Detailed version history
            report += "## Version History\n\n"
            report += "| Version | Date | Accuracy | Tokens | Cost |\n"
            report += "|---------|------|----------|--------|------|\n"
            
            for entry in performance_history:
                version = entry.get('version', 'unknown')
                timestamp = entry.get('timestamp', '')
                date = timestamp.split('T')[0] if timestamp else 'unknown'
                accuracy = entry.get('accuracy', 0)
                tokens = entry.get('tokens', {}).get('total', 0)
                cost = entry.get('cost', 0)
                
                report += f"| {version} | {date} | {accuracy:.2f}% | {tokens} | ${cost:.4f} |\n"
            
            # Recommendations
            report += "\n## Recommendations\n\n"
            recommendations = self._generate_recommendations(analysis)
            for rec in recommendations:
                report += f"- {rec}\n"
            
            # Generate report timestamp
            report += f"\n\n---\n*Report generated: {datetime.now().isoformat()}*"
            
            return report
        
        except Exception as e:
            self.logger.error(f"Error generating performance report for '{prompt_id}': {e}")
            return f"Error generating report: {str(e)}"
    
    def compare_versions(
        self,
        prompt_id: str,
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """
        Compare performance metrics between two prompt versions.
        
        Args:
            prompt_id: Identifier for the prompt
            version1: First version string
            version2: Second version string
            
        Returns:
            Comparison data
        """
        if not self.prompt_provider:
            self.logger.warning("No prompt provider available for version comparison")
            return {}
        
        try:
            # Get performance history
            performance_history = self.prompt_provider.get_performance_history(prompt_id)
            
            # Find the entries for the specified versions
            perf1 = next((p for p in performance_history if p.get('version') == version1), {})
            perf2 = next((p for p in performance_history if p.get('version') == version2), {})
            
            if not perf1 or not perf2:
                return {
                    'prompt_id': prompt_id,
                    'error': 'One or both versions not found in performance history'
                }
            
            # Compare metrics
            accuracy_diff = perf2.get('accuracy', 0) - perf1.get('accuracy', 0)
            token_diff = perf2.get('tokens', {}).get('total', 0) - perf1.get('tokens', {}).get('total', 0)
            cost_diff = perf2.get('cost', 0) - perf1.get('cost', 0)
            
            # Calculate percentage changes
            accuracy_pct = (accuracy_diff / perf1.get('accuracy', 1)) * 100 if perf1.get('accuracy', 0) != 0 else 0
            token_pct = (token_diff / perf1.get('tokens', {}).get('total', 1)) * 100 if perf1.get('tokens', {}).get('total', 0) != 0 else 0
            cost_pct = (cost_diff / perf1.get('cost', 1)) * 100 if perf1.get('cost', 0) != 0 else 0
            
            return {
                'prompt_id': prompt_id,
                'versions': {
                    version1: perf1,
                    version2: perf2
                },
                'differences': {
                    'accuracy': {
                        'absolute': accuracy_diff,
                        'percentage': accuracy_pct,
                        'improved': accuracy_diff > 0
                    },
                    'tokens': {
                        'absolute': token_diff,
                        'percentage': token_pct,
                        'improved': token_diff < 0  # Fewer tokens is better
                    },
                    'cost': {
                        'absolute': cost_diff,
                        'percentage': cost_pct,
                        'improved': cost_diff < 0  # Lower cost is better
                    }
                },
                'summary': self._generate_comparison_summary(accuracy_diff, token_diff, cost_diff)
            }
        
        except Exception as e:
            self.logger.error(f"Error comparing versions for '{prompt_id}': {e}")
            return {
                'prompt_id': prompt_id,
                'error': str(e)
            }
    
    # Helper methods
    
    def _extract_performance_data(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract performance data from test results.
        
        Args:
            test_results: Test results dictionary
            
        Returns:
            Performance data dictionary
        """
        performance_data = {
            'timestamp': datetime.now().isoformat(),
            'accuracy': 0,
            'tokens': {
                'prompt': 0,
                'completion': 0,
                'total': 0
            },
            'cost': 0.0,
            'validation_success': False
        }
        
        # Extract data from each provider's results
        provider_accuracies = []
        provider_tokens = []
        provider_costs = []
        
        for provider, provider_results in test_results.items():
            if 'validation' in provider_results:
                validation = provider_results['validation']
                
                # Record accuracy
                if 'accuracy' in validation:
                    provider_accuracies.append(validation['accuracy'])
                
                # Record validation success
                if validation.get('success', False):
                    performance_data['validation_success'] = True
            
            # Record tokens and cost
            if 'usage' in provider_results:
                usage = provider_results['usage']
                tokens = {
                    'prompt': usage.get('prompt_tokens', 0),
                    'completion': usage.get('completion_tokens', 0),
                    'total': usage.get('total_tokens', 0)
                }
                provider_tokens.append(tokens)
                provider_costs.append(usage.get('total_cost', 0.0))
        
        # Calculate averages
        if provider_accuracies:
            performance_data['accuracy'] = sum(provider_accuracies) / len(provider_accuracies)
        
        if provider_tokens:
            avg_tokens = {
                'prompt': sum(t['prompt'] for t in provider_tokens) / len(provider_tokens),
                'completion': sum(t['completion'] for t in provider_tokens) / len(provider_tokens),
                'total': sum(t['total'] for t in provider_tokens) / len(provider_tokens)
            }
            performance_data['tokens'] = avg_tokens
        
        if provider_costs:
            performance_data['cost'] = sum(provider_costs) / len(provider_costs)
        
        return performance_data
    
    def _calculate_trend(
        self, 
        values: List[float], 
        decreasing_is_good: bool = False
    ) -> float:
        """
        Calculate the trend of a metric.
        
        Args:
            values: List of values
            decreasing_is_good: Whether a decrease is considered an improvement
            
        Returns:
            Percentage change (positive = improvement)
        """
        if not values or len(values) < 2:
            return 0.0
        
        first_val = values[0] if values[0] != 0 else 0.001  # Avoid division by zero
        last_val = values[-1]
        
        pct_change = ((last_val - first_val) / first_val) * 100
        
        # If decreasing is good, invert the sign
        if decreasing_is_good:
            pct_change = -pct_change
        
        return pct_change
    
    def _generate_overall_assessment(
        self,
        accuracy_improvement: float,
        token_efficiency: float,
        cost_efficiency: float
    ) -> str:
        """
        Generate an overall assessment based on trends.
        
        Args:
            accuracy_improvement: Accuracy trend
            token_efficiency: Token efficiency trend
            cost_efficiency: Cost efficiency trend
            
        Returns:
            Assessment string
        """
        # Weight the factors (accuracy is more important)
        weighted_score = (accuracy_improvement * 0.6) + (token_efficiency * 0.2) + (cost_efficiency * 0.2)
        
        if weighted_score > 10:
            return "Significant improvement across all metrics"
        elif weighted_score > 5:
            return "Moderate improvement with some trade-offs"
        elif weighted_score > 0:
            return "Slight improvement, but optimization may be needed"
        elif weighted_score > -5:
            return "Stable performance with minor degradation"
        else:
            return "Performance degradation, prompt revision recommended"
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations based on performance analysis.
        
        Args:
            analysis: Performance analysis data
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Check accuracy trend
        accuracy_trend = analysis['trends']['accuracy']
        if accuracy_trend['improvement'] < 0:
            recommendations.append("Focus on improving extraction accuracy in your next prompt iteration.")
        elif accuracy_trend['improvement'] < 5 and analysis['best_accuracy'] < 90:
            recommendations.append("Continue optimizing for accuracy, with special attention to specific fields.")
        
        # Check token trend
        token_trend = analysis['trends']['tokens']
        if token_trend['improvement'] < 0:
            recommendations.append("Consider making your prompt more concise to reduce token usage.")
        
        # Check cost trend
        cost_trend = analysis['trends']['cost']
        if cost_trend['improvement'] < 0:
            recommendations.append("Monitor increasing costs - consider prompt simplification or fewer examples.")
        
        # General recommendations
        if analysis['versions_count'] < 3:
            recommendations.append("Create more versions to establish clear performance trends.")
        
        if analysis['best_version'] != analysis['latest_version']:
            recommendations.append(f"Consider reverting to the best performing version ({analysis['best_version']}) as a baseline for further improvements.")
        
        # If no recommendations, add a general one
        if not recommendations:
            if analysis['best_accuracy'] > 95:
                recommendations.append("Current prompt is performing well. Consider testing with more diverse inputs.")
            else:
                recommendations.append("Continue iterative improvements with a focus on specific extraction challenges.")
        
        return recommendations
    
    def _generate_comparison_summary(
        self,
        accuracy_diff: float,
        token_diff: float,
        cost_diff: float
    ) -> str:
        """
        Generate a comparison summary between two versions.
        
        Args:
            accuracy_diff: Difference in accuracy
            token_diff: Difference in token usage
            cost_diff: Difference in cost
            
        Returns:
            Summary string
        """
        parts = []
        
        # Accuracy
        if accuracy_diff > 5:
            parts.append(f"significantly more accurate (+{accuracy_diff:.2f}%)")
        elif accuracy_diff > 1:
            parts.append(f"more accurate (+{accuracy_diff:.2f}%)")
        elif accuracy_diff < -5:
            parts.append(f"significantly less accurate ({accuracy_diff:.2f}%)")
        elif accuracy_diff < -1:
            parts.append(f"less accurate ({accuracy_diff:.2f}%)")
        
        # Tokens
        if token_diff < -50:
            parts.append(f"uses significantly fewer tokens (-{abs(token_diff):.0f})")
        elif token_diff < -10:
            parts.append(f"uses fewer tokens (-{abs(token_diff):.0f})")
        elif token_diff > 50:
            parts.append(f"uses significantly more tokens (+{token_diff:.0f})")
        elif token_diff > 10:
            parts.append(f"uses more tokens (+{token_diff:.0f})")
        
        # Cost
        if cost_diff < -0.01:
            parts.append(f"more cost-effective (-${abs(cost_diff):.4f})")
        elif cost_diff > 0.01:
            parts.append(f"more expensive (+${cost_diff:.4f})")
        
        if not parts:
            return "No significant difference between versions"
        
        return f"The newer version is {', '.join(parts)}"