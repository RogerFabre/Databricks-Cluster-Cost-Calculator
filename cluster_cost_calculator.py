#  cluster_cost_calculator_ui_improved.py

import streamlit as st
from math import ceil
import pandas as pd
import altair as alt

# Define the VMInstance class
class VMInstance:
    def __init__(self, name, vCPUs, DBUs, cost_per_hour, RAM_GB):
        self.name = name
        self.vCPUs = vCPUs
        self.DBUs = DBUs
        self.cost_per_hour = cost_per_hour
        self.RAM_GB = RAM_GB  # Memòria RAM en GB

# Define cost calculation functions
def calcular_cost_job_cluster(driver_cost_per_hour, worker_cost_per_hour, total_DBUs, cost_dbu_job, temps_overhead_min, temps_execucio_min):
    """
    Calcula el cost total per tasca en un Job Cluster.

    Parameters:
    - driver_cost_per_hour: Cost per hora del driver.
    - worker_cost_per_hour: Cost per hora dels workers.
    - total_DBUs: Total de DBUs utilitzades.
    - cost_dbu_job: Cost per DBU-hora en Job Cluster.
    - temps_overhead_min: Temps d'overhead en minuts.
    - temps_execucio_min: Temps d'execució per tasca en minuts.

    Returns:
    - cost_total_per_tasca_job: Cost total per tasca en Job Cluster.
    - cost_vm_total: Cost total de VM durant l'overhead i execució.
    - cost_dbu_execucio: Cost de DBUs durant l'execució.
    - temps_total_min: Temps total actiu en minuts.
    """
    # Temps total actiu incloent overhead
    temps_total_min = temps_overhead_min + temps_execucio_min

    # Càlcul del Cost de les VM durant l'overhead i l'execució
    cost_vm_total = (temps_total_min / 60) * (driver_cost_per_hour + worker_cost_per_hour)

    # Càlcul del Cost de les DBUs durant l'execució
    cost_dbu_execucio = (temps_execucio_min / 60) * total_DBUs * cost_dbu_job

    # Càlcul del Cost Total per Tasca
    cost_total_per_tasca_job = cost_vm_total + cost_dbu_execucio

    return cost_total_per_tasca_job, cost_vm_total, cost_dbu_execucio, temps_total_min

def calcular_cost_all_purpose(driver_cost_per_hour, workers_cost_per_hour, total_DBUs, cost_dbu_all_purpose, temps_total_actiu_min):
    """
    Calcula el cost total en un All-Purpose Cluster.

    Parameters:
    - driver_cost_per_hour: Cost per hora del driver.
    - workers_cost_per_hour: Cost per hora dels workers.
    - total_DBUs: Total de DBUs utilitzades.
    - cost_dbu_all_purpose: Cost per DBU-hora en All-Purpose Cluster.
    - temps_total_actiu_min: Temps total actiu en minuts.

    Returns:
    - cost_total_all_purpose: Cost total en All-Purpose Cluster.
    - cost_dbu_all_purpose_per_hour: Cost de DBUs per hora.
    - cost_vm_all_purpose_per_hour: Cost de VM per hora.
    - cost_total_per_hour_all_purpose: Cost total per hora en All-Purpose Cluster.
    """
    # Càlcul del Cost de les DBUs per hora
    cost_dbu_all_purpose_per_hour = total_DBUs * cost_dbu_all_purpose

    # Càlcul del Cost de les VM per hora
    cost_vm_all_purpose_per_hour = driver_cost_per_hour + workers_cost_per_hour

    # Càlcul del Cost Total per hora All-Purpose
    cost_total_per_hour_all_purpose = cost_dbu_all_purpose_per_hour + cost_vm_all_purpose_per_hour

    # Càlcul del Cost Total All-Purpose durant l'Actiu
    cost_total_all_purpose = (temps_total_actiu_min / 60) * cost_total_per_hour_all_purpose

    return cost_total_all_purpose, cost_dbu_all_purpose_per_hour, cost_vm_all_purpose_per_hour, cost_total_per_hour_all_purpose

# Streamlit App
def main():
    # Configura la pàgina
    st.set_page_config(page_title="📊 Cluster Cost Calculator", layout="wide", initial_sidebar_state="expanded")
    
    # Títol principal
    st.title("📊 Cluster Cost Calculator")
    st.markdown("""
    Aquesta aplicació permet calcular els costos i els temps d'execució dels **Job Clusters** i **All-Purpose Clusters** segons la seva configuració i les tasques que han de realitzar.
    """)
    
    # Barra lateral per a inputs
    st.sidebar.header("🛠️ Configuració")
    
    # Define available VM instances (incloent RAM)
    instancies = [
        VMInstance('DS4_V2', 8, 1.5, 0.5219, 32),
        VMInstance('D4A_V4', 4, 0.75, 0.2207, 16),
        VMInstance('D8A_V4', 8, 1.5, 0.4414, 32),
        VMInstance('E4DS_V5', 4, 1.5, 0.3320, 24),
        VMInstance('D4DS_V5', 4, 1.0, 0.2610, 16)
    ]
    
    # Instance selection
    instance_names = [inst.name for inst in instancies]
    selected_instance_name = st.sidebar.selectbox("🔍 Tipus d'instància", instance_names)
    instancia = next(inst for inst in instancies if inst.name == selected_instance_name)
    
    st.sidebar.markdown("---")
    
    # User inputs
    temps_execucio_per_tasca_min = st.sidebar.number_input("⏱️ Temps d'execució per tasca (minuts)", min_value=0.1, value=10.0, step=0.1)
    nombre_tasques = st.sidebar.number_input("🔢 Nombre de tasques", min_value=1, value=100, step=1)
    nombre_workers_all_purpose = st.sidebar.number_input("👥 Nombre de workers (All-Purpose)", min_value=1, value=5, step=1)
    
    # Constants
    temps_overhead_min = 2.5
    cost_dbu_job = 0.288
    cost_dbu_all_purpose = 0.528
    
    # Configuració Job Cluster
    nodes_job_driver = 1
    nodes_job_workers = 1
    dbus_job = (nodes_job_driver + nodes_job_workers) * instancia.DBUs
    cost_vm_job_driver = nodes_job_driver * instancia.cost_per_hour
    cost_vm_job_workers = nodes_job_workers * instancia.cost_per_hour
    cost_vm_job_total = cost_vm_job_driver + cost_vm_job_workers
    
    # Calculate Job Cluster cost per task
    cost_per_tasca_job, cost_vm_total_job, cost_dbu_execucio_job, temps_total_min_job = calcular_cost_job_cluster(
        driver_cost_per_hour=cost_vm_job_driver,
        worker_cost_per_hour=cost_vm_job_workers,
        total_DBUs=dbus_job,
        cost_dbu_job=cost_dbu_job,
        temps_overhead_min=temps_overhead_min,
        temps_execucio_min=temps_execucio_per_tasca_min
    )
    cost_total_job = nombre_tasques * cost_per_tasca_job
    
    # Configuració All-Purpose Cluster
    nodes_all_purpose_driver = 1
    nodes_all_purpose_workers = nombre_workers_all_purpose
    dbus_all_purpose = (nodes_all_purpose_driver + nodes_all_purpose_workers) * instancia.DBUs
    cost_vm_all_purpose_driver = nodes_all_purpose_driver * instancia.cost_per_hour
    cost_vm_all_purpose_workers = nodes_all_purpose_workers * instancia.cost_per_hour
    cost_vm_all_purpose_total = cost_vm_all_purpose_driver + cost_vm_all_purpose_workers
    
    # Calculate All-Purpose Cluster cost
    tasks_per_worker = 1  # Limiting to one task per worker
    total_parallel_tasks = nombre_workers_all_purpose * tasks_per_worker
    nombre_onades = ceil(nombre_tasques / total_parallel_tasks)
    temps_execucio_total_min = nombre_onades * temps_execucio_per_tasca_min
    temps_total_actiu_min = temps_overhead_min + temps_execucio_total_min
    
    cost_total_all_purpose, cost_dbu_all_purpose_per_hour, cost_vm_all_purpose_per_hour, cost_total_per_hour_all_purpose = calcular_cost_all_purpose(
        driver_cost_per_hour=cost_vm_all_purpose_driver,
        workers_cost_per_hour=cost_vm_all_purpose_workers,
        total_DBUs=dbus_all_purpose,
        cost_dbu_all_purpose=cost_dbu_all_purpose,
        temps_total_actiu_min=temps_total_actiu_min
    )
    
    # Layout principal amb columnes
    col1, col2 = st.columns(2)
    
    with col1:
        st.header("📈 Resultats Job Cluster")
        
        # Secció de Detalls del Clúster
        with st.expander("📋 Detalls del Job Cluster"):
            st.markdown(f"""
            - **Nombre de Drivers**: {nodes_job_driver}
            - **Nombre de Workers**: {nodes_job_workers}
            - **vCPUs per Node**: {instancia.vCPUs}
            - **DBUs per Node**: {instancia.DBUs}
            - **RAM per Node**: {instancia.RAM_GB} GB
            """)
        
        # Secció de Càlculs de Cost
        with st.expander("💰 Càlculs de Cost Job Cluster"):
            st.markdown(f"""
            **Passos per calcular el cost total en un Job Cluster:**
            
            1. **Càlcul del Cost de les VM durant l'overhead i l'execució**:
                - **Fórmula**: Cost VM Total = (Temps Total Actiu / 60) * (Cost Driver + Cost Workers)
                - **Aplicació**: Cost VM Total = ({temps_overhead_min} + {temps_execucio_per_tasca_min}) / 60 * ({cost_vm_job_driver} + {cost_vm_job_workers}) = **€{cost_vm_total_job:.4f}**
            
            2. **Càlcul del Cost de les DBUs durant l'execució**:
                - **Fórmula**: Cost DBU Execució = (Temps Execució per Tasca / 60) * Total DBUs * Cost per DBU-hora
                - **Aplicació**: Cost DBU Execució = {temps_execucio_per_tasca_min} / 60 * {dbus_job} * {cost_dbu_job} = **€{cost_dbu_execucio_job:.4f}**
            
            3. **Càlcul del Cost Total per Tasca**:
                - **Fórmula**: Cost Total per Tasca = Cost VM Total + Cost DBU Execució
                - **Aplicació**: Cost Total per Tasca = €{cost_vm_total_job:.4f} + €{cost_dbu_execucio_job:.4f} = **€{cost_per_tasca_job:.4f}**
            
            4. **Càlcul del Cost Total del Job Cluster**:
                - **Fórmula**: Cost Total Job Cluster = Nombre de Tasques * Cost Total per Tasca
                - **Aplicació**: Cost Total Job Cluster = {nombre_tasques} * €{cost_per_tasca_job:.4f} = **€{cost_total_job:.4f}**
            """)
        
        # Metrics per Job Cluster
        st.metric(label="**Cost per tasca**", value=f"€{cost_per_tasca_job:.4f}")
        st.metric(label="**Cost total**", value=f"€{cost_total_job:.4f}")
        st.metric(label="**Temps Total Actiu**", value=f"{temps_total_min_job} minuts")
    
    with col2:
        st.header("📉 Resultats All-Purpose Cluster")
        
        # Secció de Detalls del Clúster
        with st.expander("📋 Detalls de l'All-Purpose Cluster"):
            st.markdown(f"""
            - **Nombre de Drivers**: {nodes_all_purpose_driver}
            - **Nombre de Workers**: {nodes_all_purpose_workers}
            - **vCPUs per Node**: {instancia.vCPUs}
            - **DBUs per Node**: {instancia.DBUs}
            - **RAM per Node**: {instancia.RAM_GB} GB
            """)
        
        # Secció de Càlculs de Cost
        with st.expander("💰 Càlculs de Cost All-Purpose Cluster"):
            st.markdown(f"""
            **Passos per calcular el cost total en un All-Purpose Cluster:**
            
            1. **Càlcul del Cost de les DBUs per hora**:
                - **Fórmula**: Cost DBU All-Purpose per hora = Total DBUs * Cost per DBU-hora
                - **Aplicació**: Cost DBU All-Purpose per hora = {dbus_all_purpose} * {cost_dbu_all_purpose} = **€{cost_dbu_all_purpose_per_hour:.4f} €/h**
            
            2. **Càlcul del Cost de les VM per hora**:
                - **Fórmula**: Cost VM All-Purpose per hora = Cost Driver + Cost Workers
                - **Aplicació**: Cost VM All-Purpose per hora = {cost_vm_all_purpose_driver} + {cost_vm_all_purpose_workers} = **€{cost_vm_all_purpose_per_hour:.4f} €/h**
            
            3. **Càlcul del Cost Total per hora All-Purpose**:
                - **Fórmula**: Cost Total per hora All-Purpose = Cost DBU All-Purpose per hora + Cost VM All-Purpose per hora
                - **Aplicació**: Cost Total per hora All-Purpose = €{cost_dbu_all_purpose_per_hour:.4f} €/h + €{cost_vm_all_purpose_per_hour:.4f} €/h = **€{cost_total_per_hour_all_purpose:.4f} €/h**
            
            4. **Càlcul del Cost Total All-Purpose durant l'Actiu**:
                - **Fórmula**: Cost Total All-Purpose = (Temps Total Actiu / 60) * Cost Total per hora All-Purpose
                - **Aplicació**: Cost Total All-Purpose = {temps_total_actiu_min} / 60 * €{cost_total_per_hour_all_purpose:.4f} €/h = **€{cost_total_all_purpose:.4f}**
            """)
        
        # Metrics per All-Purpose Cluster
        st.metric(label="**Cost total**", value=f"€{cost_total_all_purpose:.4f}")
        st.metric(label="**Temps Total Actiu**", value=f"{temps_total_actiu_min} minuts")
    
    # Visualització gràfica de comparació de costos
    st.header("📊 Comparació de Costos")
    
    # Dades per al gràfic
    data_cost = pd.DataFrame({
        'Clúster': ['Job Cluster', 'All-Purpose Cluster'],
        'Cost Total (€)': [cost_total_job, cost_total_all_purpose]
    })
    
    # Crear gràfic de barres per costos
    bar_chart_cost = alt.Chart(data_cost).mark_bar().encode(
        x=alt.X('Clúster', sort=None, title='Tipus de Clúster'),
        y=alt.Y('Cost Total (€)', title='Cost Total (€)'),
        color='Clúster'
    ).properties(
        width=600,
        height=400,
        title='Comparació dels Costos Totals'
    )
    
    st.altair_chart(bar_chart_cost, use_container_width=True)
    
    # Visualització gràfica de comparació de temps
    st.header("⏰ Comparació de Temps d'Execució")
    
    # Dades per al gràfic de temps
    data_time = pd.DataFrame({
        'Clúster': ['Job Cluster', 'All-Purpose Cluster'],
        'Temps Total Actiu (minuts)': [temps_total_min_job, temps_total_actiu_min]
    })
    
    # Crear gràfic de barres per temps
    bar_chart_time = alt.Chart(data_time).mark_bar().encode(
        x=alt.X('Clúster', sort=None, title='Tipus de Clúster'),
        y=alt.Y('Temps Total Actiu (minuts)', title='Temps Total Actiu (minuts)'),
        color='Clúster'
    ).properties(
        width=600,
        height=400,
        title='Comparació dels Temps Totals Actius'
    )
    
    st.altair_chart(bar_chart_time, use_container_width=True)
    
    # Feedback Visual addicional: Optimalitat en Temps vs Cost
    st.header("📈 Optimalitat en Temps vs Cost")
    
    # Creació d'un gràfic de dispersió combinant cost i temps
    data_optimal = pd.DataFrame({
        'Clúster': ['Job Cluster', 'All-Purpose Cluster'],
        'Cost Total (€)': [cost_total_job, cost_total_all_purpose],
        'Temps Total Actiu (minuts)': [temps_total_min_job, temps_total_actiu_min]
    })
    
    scatter_chart = alt.Chart(data_optimal).mark_circle(size=100).encode(
        x=alt.X('Cost Total (€)', title='Cost Total (€)'),
        y=alt.Y('Temps Total Actiu (minuts)', title='Temps Total Actiu (minuts)'),
        color='Clúster',
        tooltip=['Clúster', 'Cost Total (€)', 'Temps Total Actiu (minuts)']
    ).properties(
        width=600,
        height=400,
        title='Optimalitat en Temps vs Cost'
    )
    
    st.altair_chart(scatter_chart, use_container_width=True)
    
    # Final Results and Conclusion
    st.header("🏆 Resultats Finals")
    st.write(f"**Cost total Job Clusters:** €{cost_total_job:.4f}")
    st.write(f"**Cost total All-Purpose:** €{cost_total_all_purpose:.4f}")
    st.write(f"**Temps total actiu Job Cluster:** {temps_total_min_job} minuts")
    st.write(f"**Temps total actiu All-Purpose Cluster:** {temps_total_actiu_min} minuts")
    
    diferencia_cost = abs(cost_total_job - cost_total_all_purpose)
    if cost_total_job < cost_total_all_purpose:
        estalvi = diferencia_cost
        percentatge_estalvi = (diferencia_cost / cost_total_all_purpose) * 100
        st.success(f"La opció més econòmica és **Job Clusters**")
        st.write(f"**Estalvi en Cost:** €{estalvi:.4f}")
        st.write(f"**Percentatge d'estalvi en Cost:** {percentatge_estalvi:.2f}%")
    else:
        estalvi = diferencia_cost
        percentatge_estalvi = (diferencia_cost / cost_total_job) * 100
        st.success(f"La opció més econòmica és **All-Purpose**")
        st.write(f"**Estalvi en Cost:** €{estalvi:.4f}")
        st.write(f"**Percentatge d'estalvi en Cost:** {percentatge_estalvi:.2f}%")
    
    # Footer amb informació addicional
    st.markdown("---")
    st.markdown("""
    📝 **Nota**: Aquests càlculs són aproximacions i poden variar segons la naturalesa específica de les tasques, la configuració del clúster i altres factors operatius.
    """)

if __name__ == "__main__":
    main()
