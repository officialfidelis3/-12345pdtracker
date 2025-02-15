import pandas as pd
from datetime import datetime, timedelta

def calculate_equipment_metrics(records):
    """Calculate maintenance metrics for each equipment"""
    if not records or len(records) == 0:
        return pd.DataFrame()
    
    # Create DataFrame with proper column names
    columns = ['id', 'date', 'shift', 'line', 'start_time', 'end_time', 
              'duration', 'equipment', 'issue_type', 'issue_description',
              'action_taken', 'responsible_person', 'remarks', 'created_at']
    df = pd.DataFrame(records, columns=columns)
    
    # Convert date to datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by equipment
    equipment_stats = []
    
    for equipment in df['equipment'].unique():
        equip_data = df[df['equipment'] == equipment]
        
        # Sort by date
        equip_data = equip_data.sort_values('date')
        
        # Calculate metrics
        total_failures = len(equip_data)
        total_downtime = equip_data['duration'].sum()
        avg_downtime = equip_data['duration'].mean()
        
        # Calculate days between failures
        if len(equip_data) > 1:
            date_diffs = equip_data['date'].diff().dropna()
            mtbf = date_diffs.mean().days
            last_failure = equip_data['date'].max()
            
            # Predict next failure
            next_predicted = last_failure + timedelta(days=mtbf)
            
            # Recommend maintenance before predicted failure
            maintenance_date = next_predicted - timedelta(days=max(2, int(mtbf * 0.2)))
        else:
            mtbf = None
            next_predicted = None
            maintenance_date = None
            
        equipment_stats.append({
            'equipment': equipment,
            'total_failures': total_failures,
            'total_downtime': total_downtime,
            'avg_downtime': round(avg_downtime, 2) if not pd.isna(avg_downtime) else 0,
            'mtbf_days': round(mtbf, 1) if mtbf else None,
            'next_predicted_failure': next_predicted,
            'recommended_maintenance': maintenance_date,
            'failure_rate': round(total_failures / (
                (df['date'].max() - df['date'].min()).days + 1
            ) * 30, 2)  # failures per month
        })
    
    return pd.DataFrame(equipment_stats)

def get_maintenance_recommendations(records, days_threshold=7):
    """Get maintenance recommendations for equipment"""
    metrics_df = calculate_equipment_metrics(records)
    
    if metrics_df.empty:
        return []
    
    current_date = datetime.now()
    recommendations = []
    
    for _, row in metrics_df.iterrows():
        if pd.isna(row['recommended_maintenance']):
            continue
            
        days_until_maintenance = (row['recommended_maintenance'] - current_date).days
        
        if days_until_maintenance <= days_threshold:
            recommendations.append({
                'equipment': row['equipment'],
                'days_until_maintenance': days_until_maintenance,
                'mtbf_days': row['mtbf_days'],
                'failure_rate': row['failure_rate'],
                'avg_downtime': row['avg_downtime']
            })
    
    return sorted(recommendations, key=lambda x: x['days_until_maintenance'])
