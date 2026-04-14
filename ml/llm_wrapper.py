def enrich_with_llm(data):
    cost = data.get("cost", 0)
    severity = data.get("severity", "low")
    service = data.get("service", "unknown").lower()
    team = data.get("team", "unknown")


    if severity == "high":
        level = "critical"
    elif severity == "medium":
        level = "moderate"
    else:
        level = "low"


    if service == "compute":
        root = "Possible over-provisioned instances or autoscaling misconfiguration"
        action = "Check EC2/VM scaling policies and terminate idle instances"

    elif service == "storage":
        root = "Unoptimized storage usage or redundant backups"
        action = "Remove unused storage volumes and enable lifecycle policies"

    elif service == "networking":
        root = "Unexpected data transfer spike or misconfigured routing"
        action = "Audit outbound traffic and CDN usage"

    elif service == "managed_services":
        root = "Inefficient managed service usage or burst scaling"
        action = "Review service tiers and optimize configurations"

    else:
        root = "General anomaly in cloud usage pattern"
        action = "Investigate recent deployments and logs"

    if cost > 4000:
        impact = "very high"
        savings = "$2000-$7000"
        insight = f"Severe cost spike detected ({level}) — immediate attention required"

    elif cost > 2000:
        impact = "high"
        savings = "$1000-$3000"
        insight = f"Significant cost anomaly detected ({level})"

    elif cost > 800:
        impact = "moderate"
        savings = "$300-$1200"
        insight = f"Moderate deviation from normal spend"

    else:
        impact = "low"
        savings = "$50-$300"
        insight = f"Minor anomaly — within acceptable variation"


    return {
        "insight": insight,
        "root_cause": f"{root} (Team: {team})",
        "action": action,
        "savings": savings
    }