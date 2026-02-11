from typing import Dict, Any
import json

class QualityValidatorMCP:
    """
    Validates output quality
    Rates results on multiple dimensions
    """
    
    async def validate(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate result quality
        """
        
        # Extract quality metrics
        content = str(result.get("content", ""))
        data = result.get("data", {})
        errors = result.get("errors", [])
        
        # Accuracy check
        accuracy_score = 10.0
        if errors:
            accuracy_score = max(0, 10 - len(errors))
        
        # Completeness check
        completeness_score = 10.0
        if isinstance(data, dict):
            if len(data) == 0:
                completeness_score = 0
            else:
                completeness_score = min(10, len(data) / 5 * 10)
        elif isinstance(data, list):
            completeness_score = min(10, len(data) / 100 * 10)
        
        # Consistency check
        consistency_score = 9.0
        if "None" in content or "null" in content:
            consistency_score -= 1
        if "error" in content.lower():
            consistency_score -= 2
        
        # Format check
        format_score = 9.5
        try:
            if isinstance(data, str):
                json.loads(data)
        except:
            format_score = 7.0
        
        # Overall quality
        overall_quality = (
            accuracy_score * 0.3 +
            completeness_score * 0.3 +
            consistency_score * 0.2 +
            format_score * 0.2
        ) / 10
        
        validation = {
            "accuracy_score": round(accuracy_score / 10, 2),
            "completeness_score": round(completeness_score / 10, 2),
            "consistency_score": round(consistency_score / 10, 2),
            "format_score": round(format_score / 10, 2),
            "overall_quality": round(overall_quality, 2),
            "quality_grade": "Excellent" if overall_quality > 0.9 else "Good" if overall_quality > 0.75 else "Fair" if overall_quality > 0.6 else "Poor",
            "issues": errors[:3] if errors else [],
            "recommendations": []
        }
        
        # Add recommendations
        if validation["accuracy_score"] < 0.8:
            validation["recommendations"].append("Improve error handling")
        if validation["completeness_score"] < 0.7:
            validation["recommendations"].append("Return more complete data")
        if validation["consistency_score"] < 0.8:
            validation["recommendations"].append("Ensure consistent output format")
        
        return validation

# Create global instance
quality_validator = QualityValidatorMCP()