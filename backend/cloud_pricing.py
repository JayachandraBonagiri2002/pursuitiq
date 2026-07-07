"""
cloud_pricing.py — Live cloud pricing from Azure and AWS public APIs.

Both APIs are free and require NO authentication.
This module dynamically determines which services to price based on the RFP
requirements — no hardcoded rates. Everything is fetched live.

Used by Agent 5 to ground pricing calculations in actual infrastructure costs.
"""

import logging
import httpx

logger = logging.getLogger(__name__)

AZURE_PRICING_URL = "https://prices.azure.com/api/retail/prices"
AWS_PRICING_URL = "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws"


# ─── Service inference from RFP requirements ─────────────────────────────────

AZURE_SERVICE_MAP = {
    "virtual machines": "Virtual Machines",
    "vm": "Virtual Machines",
    "compute": "Virtual Machines",
    "server": "Virtual Machines",
    "kubernetes": "Azure Kubernetes Service",
    "k8s": "Azure Kubernetes Service",
    "container": "Azure Kubernetes Service",
    "docker": "Azure Kubernetes Service",
    "aks": "Azure Kubernetes Service",
    "sql": "Azure SQL Database",
    "database": "Azure SQL Database",
    "rds": "Azure SQL Database",
    "postgresql": "Azure Database for PostgreSQL",
    "postgres": "Azure Database for PostgreSQL",
    "mysql": "Azure Database for MySQL",
    "cosmos": "Azure Cosmos DB",
    "nosql": "Azure Cosmos DB",
    "mongodb": "Azure Cosmos DB",
    "storage": "Storage",
    "blob": "Storage",
    "object storage": "Storage",
    "s3": "Storage",
    "app service": "Azure App Service",
    "web app": "Azure App Service",
    "paas": "Azure App Service",
    "functions": "Azure Functions",
    "serverless": "Azure Functions",
    "lambda": "Azure Functions",
    "event-driven": "Azure Functions",
    "cdn": "Azure CDN",
    "content delivery": "Azure CDN",
    "cloudfront": "Azure CDN",
    "load balancer": "Load Balancer",
    "networking": "Virtual Network",
    "vpn": "VPN Gateway",
    "firewall": "Azure Firewall",
    "waf": "Azure Firewall",
    "monitoring": "Azure Monitor",
    "observability": "Azure Monitor",
    "logging": "Azure Monitor",
    "siem": "Microsoft Sentinel",
    "security": "Microsoft Defender for Cloud",
    "devops": "Azure DevOps",
    "ci/cd": "Azure DevOps",
    "pipeline": "Azure DevOps",
    "ai": "Azure OpenAI Service",
    "machine learning": "Azure Machine Learning",
    "ml": "Azure Machine Learning",
    "cognitive": "Azure Cognitive Services",
    "redis": "Azure Cache for Redis",
    "cache": "Azure Cache for Redis",
    "api management": "API Management",
    "api gateway": "API Management",
    "service bus": "Service Bus",
    "messaging": "Service Bus",
    "event hub": "Event Hubs",
    "streaming": "Event Hubs",
    "kafka": "Event Hubs",
    "backup": "Backup",
    "disaster recovery": "Azure Site Recovery",
    "dr": "Azure Site Recovery",
}

AWS_SERVICE_MAP = {
    "virtual machines": "AmazonEC2",
    "vm": "AmazonEC2",
    "compute": "AmazonEC2",
    "server": "AmazonEC2",
    "ec2": "AmazonEC2",
    "kubernetes": "AmazonEKS",
    "k8s": "AmazonEKS",
    "container": "AmazonECS",
    "docker": "AmazonECS",
    "ecs": "AmazonECS",
    "eks": "AmazonEKS",
    "sql": "AmazonRDS",
    "database": "AmazonRDS",
    "rds": "AmazonRDS",
    "postgresql": "AmazonRDS",
    "postgres": "AmazonRDS",
    "mysql": "AmazonRDS",
    "dynamodb": "AmazonDynamoDB",
    "nosql": "AmazonDynamoDB",
    "mongodb": "AmazonDocDB",
    "storage": "AmazonS3",
    "blob": "AmazonS3",
    "object storage": "AmazonS3",
    "s3": "AmazonS3",
    "serverless": "AWSLambda",
    "lambda": "AWSLambda",
    "functions": "AWSLambda",
    "event-driven": "AWSLambda",
    "cdn": "AmazonCloudFront",
    "content delivery": "AmazonCloudFront",
    "cloudfront": "AmazonCloudFront",
    "load balancer": "AmazonElasticLoadBalancing",
    "elb": "AmazonElasticLoadBalancing",
    "networking": "AmazonVPC",
    "vpn": "AmazonVPC",
    "firewall": "AWSNetworkFirewall",
    "waf": "awswaf",
    "monitoring": "AmazonCloudWatch",
    "observability": "AmazonCloudWatch",
    "logging": "AmazonCloudWatch",
    "security": "AmazonGuardDuty",
    "siem": "AmazonGuardDuty",
    "devops": "AWSCodePipeline",
    "ci/cd": "AWSCodePipeline",
    "pipeline": "AWSCodePipeline",
    "ai": "AmazonBedrock",
    "machine learning": "AmazonSageMaker",
    "ml": "AmazonSageMaker",
    "redis": "AmazonElastiCache",
    "cache": "AmazonElastiCache",
    "api management": "AmazonApiGateway",
    "api gateway": "AmazonApiGateway",
    "messaging": "AmazonSQS",
    "queue": "AmazonSQS",
    "sqs": "AmazonSQS",
    "streaming": "AmazonKinesis",
    "kafka": "AmazonMSK",
    "backup": "AWSBackup",
    "disaster recovery": "AWSCloudEndure",
}


def _infer_services_from_requirements(requirements: list[str]) -> tuple[list[str], list[str]]:
    """
    Analyze RFP requirements text to determine which cloud services are needed.
    Returns (azure_services, aws_service_codes).
    """
    req_text = " ".join(requirements).lower()

    azure_services = set()
    aws_services = set()

    for keyword, azure_svc in AZURE_SERVICE_MAP.items():
        if keyword in req_text:
            azure_services.add(azure_svc)

    for keyword, aws_svc in AWS_SERVICE_MAP.items():
        if keyword in req_text:
            aws_services.add(aws_svc)

    # Always include baseline infrastructure if nothing specific found
    if not azure_services:
        azure_services = {"Virtual Machines", "Storage", "Azure SQL Database", "Azure Monitor"}
    if not aws_services:
        aws_services = {"AmazonEC2", "AmazonS3", "AmazonRDS", "AmazonCloudWatch"}

    return list(azure_services), list(aws_services)


# ─── Azure live pricing ──────────────────────────────────────────────────────

def get_azure_pricing(services: list[str] | None = None, region: str = "westeurope") -> list[dict]:
    """
    Fetch real-time Azure pricing from the public Retail Prices API.
    Dynamically queries only the services relevant to the RFP.
    """
    if services is None:
        services = ["Virtual Machines", "Storage", "Azure SQL Database", "Azure Monitor"]

    results = []
    for service in services:
        try:
            # Filter for standard consumption pricing (not Spot/Low Priority/Reserved)
            filter_query = (
                f"serviceName eq '{service}' and "
                f"armRegionName eq '{region}' and "
                f"priceType eq 'Consumption' and "
                f"contains(skuName, 'Standard') eq true"
            )
            resp = httpx.get(
                AZURE_PRICING_URL,
                params={"$filter": filter_query, "$top": "15"},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                for item in data.get("Items", []):
                    price = item.get("unitPrice", 0)
                    sku = item.get("skuName", "")
                    # Skip spot/low-priority/dev SKUs — we want production pricing
                    if price > 0 and "Spot" not in sku and "Low Priority" not in sku:
                        results.append({
                            "provider": "Azure",
                            "service": item.get("serviceName"),
                            "sku": sku,
                            "meter": item.get("meterName"),
                            "unit_price_usd": price,
                            "unit": item.get("unitOfMeasure"),
                            "region": region,
                        })
        except Exception as e:
            logger.warning(f"Azure pricing fetch failed for {service}: {e}")

    logger.info(f"Azure pricing: fetched {len(results)} live items for {len(services)} services in {region}")
    return results


# ─── AWS live pricing ────────────────────────────────────────────────────────

def get_aws_pricing(service_codes: list[str] | None = None, region: str = "eu-west-1") -> list[dict]:
    """
    Fetch real-time AWS pricing from the public Bulk Pricing API.
    Uses the free offers index API — no auth required.
    """
    if service_codes is None:
        service_codes = ["AmazonEC2", "AmazonS3", "AmazonRDS", "AmazonCloudWatch"]

    results = []
    for service_code in service_codes:
        try:
            index_url = f"{AWS_PRICING_URL}/{service_code}/current/region_index.json"
            resp = httpx.get(index_url, timeout=15)
            if resp.status_code != 200:
                logger.warning(f"AWS pricing index unavailable for {service_code} (HTTP {resp.status_code})")
                continue

            region_index = resp.json()
            regions = region_index.get("regions", {})

            region_data = regions.get(region) or regions.get("us-east-1")
            if not region_data:
                continue

            offer_url = region_data.get("currentVersionUrl")
            if not offer_url:
                continue

            # Fetch the regional offer file (can be large, use stream + limit)
            full_url = f"https://pricing.us-east-1.amazonaws.com{offer_url}"
            resp2 = httpx.get(full_url, timeout=30, headers={"Accept-Encoding": "gzip"})
            if resp2.status_code != 200:
                continue

            offer_data = resp2.json()
            products = offer_data.get("products", {})
            terms = offer_data.get("terms", {}).get("OnDemand", {})

            count = 0
            for sku_id, product in products.items():
                if count >= 10:
                    break
                attrs = product.get("attributes", {})
                # For EC2/RDS: only Linux, current gen
                if service_code in ("AmazonEC2", "AmazonRDS"):
                    if service_code == "AmazonEC2" and attrs.get("operatingSystem") != "Linux":
                        continue
                    if attrs.get("currentGeneration") == "No":
                        continue

                sku_terms = terms.get(sku_id, {})
                for offer_term in sku_terms.values():
                    price_dims = offer_term.get("priceDimensions", {})
                    for dim in price_dims.values():
                        price_per_unit = dim.get("pricePerUnit", {}).get("USD")
                        if price_per_unit and float(price_per_unit) > 0:
                            # Build a readable SKU description
                            instance_type = attrs.get("instanceType", "")
                            product_family = attrs.get("productFamily", "")
                            desc = instance_type or attrs.get("usagetype", product_family)
                            if attrs.get("vcpu") and attrs.get("memory"):
                                desc = f"{instance_type} ({attrs['vcpu']} vCPU, {attrs['memory']})"

                            results.append({
                                "provider": "AWS",
                                "service": service_code,
                                "sku": desc,
                                "meter": dim.get("description", "")[:80],
                                "unit_price_usd": float(price_per_unit),
                                "unit": dim.get("unit", ""),
                                "region": region,
                            })
                            count += 1
                            break
                    if count >= 10:
                        break

        except Exception as e:
            logger.warning(f"AWS pricing fetch failed for {service_code}: {e}")

    logger.info(f"AWS pricing: fetched {len(results)} live items for {len(service_codes)} services in {region}")
    return results


# ─── Geography mapping ───────────────────────────────────────────────────────

def _map_geography_to_regions(geography: list[str] | None) -> tuple[str, str]:
    """Map deal geography to the appropriate cloud regions."""
    azure_region = "westeurope"
    aws_region = "eu-west-1"

    if geography:
        geo_lower = " ".join(geography).lower()
        if any(x in geo_lower for x in ["usa", "us", "america", "united states"]):
            azure_region = "eastus"
            aws_region = "us-east-1"
        elif any(x in geo_lower for x in ["uk", "united kingdom", "britain"]):
            azure_region = "uksouth"
            aws_region = "eu-west-2"
        elif any(x in geo_lower for x in ["singapore", "asia"]):
            azure_region = "southeastasia"
            aws_region = "ap-southeast-1"
        elif any(x in geo_lower for x in ["australia"]):
            azure_region = "australiaeast"
            aws_region = "ap-southeast-2"
        elif any(x in geo_lower for x in ["india"]):
            azure_region = "centralindia"
            aws_region = "ap-south-1"
        elif any(x in geo_lower for x in ["uae", "middle east"]):
            azure_region = "uaenorth"
            aws_region = "me-south-1"
        elif any(x in geo_lower for x in ["japan"]):
            azure_region = "japaneast"
            aws_region = "ap-northeast-1"
        elif any(x in geo_lower for x in ["brazil", "latam", "latin america"]):
            azure_region = "brazilsouth"
            aws_region = "sa-east-1"
        elif any(x in geo_lower for x in ["canada"]):
            azure_region = "canadacentral"
            aws_region = "ca-central-1"
        elif any(x in geo_lower for x in ["korea", "south korea"]):
            azure_region = "koreacentral"
            aws_region = "ap-northeast-2"

    return azure_region, aws_region


# ─── Main entry point ────────────────────────────────────────────────────────

def get_cloud_pricing_context(geography: list[str] | None = None, requirements: list[str] | None = None) -> str:
    """
    Get formatted cloud pricing context for Agent 5's prompt.

    Dynamically determines which services to price based on RFP requirements,
    then fetches LIVE pricing from both Azure and AWS public APIs.

    Args:
        geography:    List of countries/regions from the RFP decomposition
        requirements: List of requirement texts from the RFP (used to infer services)

    Returns:
        Formatted string with real-time pricing data for the agent's prompt
    """
    azure_region, aws_region = _map_geography_to_regions(geography)

    # Infer which services are needed from the RFP requirements
    if requirements:
        azure_services, aws_service_codes = _infer_services_from_requirements(requirements)
        logger.info(f"Cloud pricing: inferred Azure={azure_services}, AWS={aws_service_codes} from requirements")
    else:
        azure_services = None
        aws_service_codes = None

    # Fetch LIVE pricing from both providers
    azure_prices = get_azure_pricing(services=azure_services, region=azure_region)
    aws_prices = get_aws_pricing(service_codes=aws_service_codes, region=aws_region)

    # Format for the agent prompt
    lines = [
        f"LIVE CLOUD PRICING (fetched in real-time from public APIs)",
        f"Regions: Azure={azure_region}, AWS={aws_region}",
        f"{'='*70}",
        "",
        "AZURE PRICING (live from Azure Retail Prices API):",
    ]

    if azure_prices:
        for p in azure_prices[:20]:
            lines.append(f"  {p['service']} | {p['sku']} | {p.get('meter', '')} | ${p['unit_price_usd']:.4f} per {p['unit']}")
    else:
        lines.append("  [Azure API unavailable — use AWS pricing below as reference]")

    lines.append("")
    lines.append("AWS PRICING (live from AWS Bulk Pricing API):")

    if aws_prices:
        for p in aws_prices[:20]:
            lines.append(f"  {p['service']} | {p['sku']} | ${p['unit_price_usd']:.6f} per {p['unit']}")
    else:
        lines.append("  [AWS API unavailable — use Azure pricing above as reference]")

    lines.append("")
    lines.append("IMPORTANT: These are LIVE prices fetched just now. Use them directly.")
    lines.append("Calculate infrastructure costs bottom-up from these unit prices.")
    lines.append("Do NOT use memorized pricing — only use the numbers above.")

    return "\n".join(lines)
