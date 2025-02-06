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
def calcular_cost_job_cluster(driver_cost_per_hour, worker_cost_per_hour, total_DBUs, cost_dbu_job,
                                startup_overhead_time, temps_execucio_min, max_parallel_tasks, total_tasks):
    """
    Calcula el cost total per tasca en un Job Cluster, considerant una limitació de tasques en paral·lel.
    """
    # Nombre d'onades necessàries
    nombre_onades_job = ceil(total_tasks / max_parallel_tasks)
    
    # Temps total actiu incloent el temps de spin-up per onada
    temps_total_min_job = nombre_onades_job * (startup_overhead_time + temps_execucio_min)
    
    # Càlcul del cost de les VM durant el spin-up i l'execució per onada
    cost_vm_total_job = ((startup_overhead_time + temps_execucio_min) / 60) * (driver_cost_per_hour + worker_cost_per_hour)
    
    # Càlcul del cost de les DBUs durant l'execució per onada
    cost_dbu_execucio_job = (temps_execucio_min / 60) * total_DBUs * cost_dbu_job
    
    # Càlcul del cost total per tasca
    cost_total_per_tasca_job = cost_vm_total_job + cost_dbu_execucio_job
    
    return cost_total_per_tasca_job, cost_vm_total_job, cost_dbu_execucio_job, temps_total_min_job, nombre_onades_job

def calcular_cost_all_purpose(driver_cost_per_hour, workers_cost_per_hour, total_DBUs, cost_dbu_all_purpose,
                              temps_total_actiu_min):
    """
    Calcula el cost total en un All-Purpose Cluster.
    """
    # Càlcul del cost de les VM per hora
    cost_vm_all_purpose_per_hour = driver_cost_per_hour + workers_cost_per_hour

    # Càlcul del cost de les DBUs per hora
    cost_dbu_all_purpose_per_hour = total_DBUs * cost_dbu_all_purpose

    # Càlcul del cost total per hora de l'All-Purpose Cluster
    cost_total_per_hour_all_purpose = cost_vm_all_purpose_per_hour + cost_dbu_all_purpose_per_hour

    # Càlcul del cost total en funció del temps actiu
    cost_total_all_purpose = (temps_total_actiu_min / 60) * cost_total_per_hour_all_purpose

    return cost_total_all_purpose, cost_dbu_all_purpose_per_hour, cost_vm_all_purpose_per_hour, cost_total_per_hour_all_purpose

# Streamlit App
def main():
    # Configure the page
    st.set_page_config(page_title="📊 Cluster Cost Calculator", layout="wide", initial_sidebar_state="expanded")
    
    # Main title with logo
    col_title, col_logo = st.columns([4, 1])
    with col_title:
        st.title("📊 Cluster Cost Calculator")
    with col_logo:
        try:
            st.image("logo.png", width=200)
        except:
            st.write("![Logo](https://via.placeholder.com/200)")
    
    st.markdown("""
    Aquesta aplicació permet calcular els costos i els temps d'execució dels **Job Clusters** i **All-Purpose Clusters** segons la seva configuració i les tasques que han de realitzar.
    """)
    
    # Summary table of instance costs
    st.header("📋 Resum dels Costos de les Instàncies")
    
    instancies = [
        VMInstance('DS4_V2', 8, 1.5, 0.5219, 32),
        VMInstance('D4A_V4', 4, 0.75, 0.2207, 16),
        VMInstance('D8A_V4', 8, 1.5, 0.4414, 32),
        VMInstance('E4DS_V5', 4, 1.5, 0.3320, 24),
        VMInstance('D4DS_V5', 4, 1.0, 0.2610, 16)
    ]
    
    data_instances = pd.DataFrame({
        'Nom de la Instància': [inst.name for inst in instancies],
        'vCPUs': [inst.vCPUs for inst in instancies],
        'DBUs': [inst.DBUs for inst in instancies],
        '€/VMs-hora': [inst.cost_per_hour for inst in instancies],
        'RAM (GB)': [inst.RAM_GB for inst in instancies]
    })
    
    data_compute_costs = pd.DataFrame({
        'Compute Type': ['All-Purpose Compute', 'Jobs Compute'],
        '€/DBU-hora': [
            f"{0.528:.3f}".replace('.', ',') + ' €',
            f"{0.288:.3f}".replace('.', ',') + ' €'
        ]
    })
    
    col_instances, col_compute_costs = st.columns(2)
    with col_instances:
        st.subheader("Instàncies Disponibles")
        st.table(data_instances)
    with col_compute_costs:
        st.subheader("Costos per Tipus de Càlcul")
        st.table(data_compute_costs)
    
    # Sidebar inputs
    st.sidebar.header("🛠️ Configuració")
    
    # --- Job Cluster Configuration ---
    st.sidebar.subheader("Job Cluster Configuració")
    instance_names = [inst.name for inst in instancies]
    selected_instance_job_driver = st.sidebar.selectbox("🔍 Tipus d'instància per al **Driver del Job Cluster**", instance_names, index=0)
    instancia_job_driver = next(inst for inst in instancies if inst.name == selected_instance_job_driver)
    
    selected_instance_job_worker = st.sidebar.selectbox("🔍 Tipus d'instància per als **Workers del Job Cluster**", instance_names, index=1)
    instancia_job_worker = next(inst for inst in instancies if inst.name == selected_instance_job_worker)
    
    nombre_workers_job = st.sidebar.number_input("👥 Nombre de workers (Job Cluster)", min_value=1, value=1, step=1)
    
    # New: Job Cluster maximum parallel tasks input
    max_parallel_tasks_job = st.sidebar.number_input("⚙️ Nombre màxim de tasques en paral·lel (Job Cluster)", 
                                                     min_value=1, value=35, step=1)
    
    st.sidebar.markdown("---")
    
    # --- All-Purpose Cluster Configuration ---
    st.sidebar.subheader("All-Purpose Cluster Configuració")
    selected_instance_all_purpose_driver = st.sidebar.selectbox("🔍 Tipus d'instància per al **Driver de l'All-Purpose Cluster**", instance_names, index=2)
    instancia_all_purpose_driver = next(inst for inst in instancies if inst.name == selected_instance_all_purpose_driver)
    
    selected_instance_all_purpose_worker = st.sidebar.selectbox("🔍 Tipus d'instància per als **Workers de l'All-Purpose Cluster**", instance_names, index=3)
    instancia_all_purpose_worker = next(inst for inst in instancies if inst.name == selected_instance_all_purpose_worker)
    
    nombre_workers_all_purpose = st.sidebar.number_input("👥 Nombre de workers (All-Purpose)", min_value=1, value=5, step=1)
    
    # New: All-Purpose Cluster maximum parallel tasks input
    max_parallel_tasks_all_purpose = st.sidebar.number_input("⚙️ Nombre màxim de tasques en paral·lel (All-Purpose)", 
                                                             min_value=1, 
                                                             value=nombre_workers_all_purpose, 
                                                             step=1)
    
    st.sidebar.markdown("---")
    
    # --- Task and Overhead Configuration ---
    temps_execucio_per_tasca_min = st.sidebar.number_input("⏱️ Temps d'execució per tasca (minuts)", min_value=0.1, value=10.0, step=0.1)
    nombre_tasques = st.sidebar.number_input("🔢 Nombre de tasques", min_value=1, value=100, step=1)
    
    # New: Startup overhead time input (in minutes)
    startup_overhead_time = st.sidebar.number_input("⏱️ Startup Overhead Time (minuts)", min_value=0.1, value=2.5, step=0.1)
    
    # Constants for DBU costs (remain unchanged)
    cost_dbu_job = 0.288
    cost_dbu_all_purpose = 0.528
    
    # -------------------------------
    # Job Cluster Calculations
    nodes_job_driver = 1
    nodes_job_workers = nombre_workers_job
    total_DBUs_job = (nodes_job_driver * instancia_job_driver.DBUs) + (nodes_job_workers * instancia_job_worker.DBUs)
    cost_vm_job_driver = nodes_job_driver * instancia_job_driver.cost_per_hour
    cost_vm_job_workers = nodes_job_workers * instancia_job_worker.cost_per_hour
    
    cost_per_tasca_job, cost_vm_total_job, cost_dbu_execucio_job, temps_total_min_job, nombre_onades_job = calcular_cost_job_cluster(
        driver_cost_per_hour=cost_vm_job_driver,
        worker_cost_per_hour=cost_vm_job_workers,
        total_DBUs=total_DBUs_job,
        cost_dbu_job=cost_dbu_job,
        startup_overhead_time=startup_overhead_time,
        temps_execucio_min=temps_execucio_per_tasca_min,
        max_parallel_tasks=max_parallel_tasks_job,
        total_tasks=nombre_tasques
    )
    cost_total_job = nombre_tasques * cost_per_tasca_job
    
    # -------------------------------
    # All-Purpose Cluster Calculations
    nodes_all_purpose_driver = 1
    nodes_all_purpose_workers = nombre_workers_all_purpose
    dbus_all_purpose = (nodes_all_purpose_driver * instancia_all_purpose_driver.DBUs) + (nodes_all_purpose_workers * instancia_all_purpose_worker.DBUs)
    cost_vm_all_purpose_driver = nodes_all_purpose_driver * instancia_all_purpose_driver.cost_per_hour
    cost_vm_all_purpose_workers = nodes_all_purpose_workers * instancia_all_purpose_worker.cost_per_hour
    
    total_parallel_tasks_all_purpose = max_parallel_tasks_all_purpose
    nombre_onades_all_purpose = ceil(nombre_tasques / total_parallel_tasks_all_purpose)
    temps_execucio_total_min_all_purpose = nombre_onades_all_purpose * temps_execucio_per_tasca_min
    temps_total_actiu_min_all_purpose = startup_overhead_time + temps_execucio_total_min_all_purpose
    
    cost_total_all_purpose, cost_dbu_all_purpose_per_hour, cost_vm_all_purpose_per_hour, cost_total_per_hour_all_purpose = calcular_cost_all_purpose(
        driver_cost_per_hour=cost_vm_all_purpose_driver,
        workers_cost_per_hour=cost_vm_all_purpose_workers,
        total_DBUs=dbus_all_purpose,
        cost_dbu_all_purpose=cost_dbu_all_purpose,
        temps_total_actiu_min=temps_total_actiu_min_all_purpose
    )
    
    # -------------------------------
    # Display Results
    col1, col2 = st.columns(2)
    with col1:
        st.header("📈 Resultats Job Cluster")
        with st.expander("📋 Detalls del Job Cluster"):
            st.markdown(f"""
            - **Tipus d'Instància del Driver**: {instancia_job_driver.name}
            - **Tipus d'Instància dels Workers**: {instancia_job_worker.name}
            - **Nombre de Drivers**: {nodes_job_driver}
            - **Nombre de Workers**: {nodes_job_workers}
            - **vCPUs per Driver**: {instancia_job_driver.vCPUs}
            - **vCPUs per Worker**: {instancia_job_worker.vCPUs}
            - **DBUs per Driver**: {instancia_job_driver.DBUs}
            - **DBUs per Worker**: {instancia_job_worker.DBUs}
            - **RAM per Driver**: {instancia_job_driver.RAM_GB} GB
            - **RAM per Worker**: {instancia_job_worker.RAM_GB} GB
            - **Nombre màxim de tasques en paral·lel**: {max_parallel_tasks_job}
            """)
        with st.expander("💰 Càlculs de Cost Job Cluster"):
            st.markdown(f"""
            **Passos per calcular el cost total en un Job Cluster:**
            
            1. **Nombre d'Onades**:
                - **Fórmula**: Nombre de Tasques / Nombre màxim de Tasques en Paral·lel
                - **Aplicació**: {nombre_tasques} tasques / {max_parallel_tasks_job} tasques = {nombre_onades_job} onades
            
            2. **Temps Total Actiu per Onada**:
                - **Fórmula**: Startup Overhead Time + Temps d'Execució per Tasca
                - **Aplicació**: {startup_overhead_time} minuts + {temps_execucio_per_tasca_min} minuts = {startup_overhead_time + temps_execucio_per_tasca_min} minuts
            
            3. **Temps Total Actiu**:
                - **Fórmula**: Nombre d'Onades * (Startup Overhead Time + Temps d'Execució per Tasca)
                - **Aplicació**: {nombre_onades_job} onades * {startup_overhead_time + temps_execucio_per_tasca_min} minuts = **{temps_total_min_job} minuts**
            
            4. **Cost de les VM per Tasca**:
                - **Fórmula**: ((Startup Overhead Time + Temps d'Execució) / 60) * (Cost Driver + Cost Workers)
                - **Aplicació**: (({startup_overhead_time} + {temps_execucio_per_tasca_min}) / 60) * (€{cost_vm_job_driver} + €{cost_vm_job_workers}) = **€{cost_vm_total_job:.4f}**
            
            5. **Cost de les DBUs durant l'Execució**:
                - **Fórmula**: (Temps d'Execució per Tasca / 60) * Total DBUs * Cost per DBU-hora 
                - **Aplicació**: ({temps_execucio_per_tasca_min} / 60) * {total_DBUs_job} DBUs * €{cost_dbu_job} = **€{cost_dbu_execucio_job:.4f}**
            
            6. **Cost Total per Tasca**:
                - **Fórmula**: Cost VM per Tasca + Cost DBU Execució
                - **Aplicació**: €{cost_vm_total_job:.4f} + €{cost_dbu_execucio_job:.4f} = **€{cost_per_tasca_job:.4f}**
            
            7. **Cost Total del Job Cluster**:
                - **Fórmula**: Nombre de Tasques * Cost Total per Tasca
                - **Aplicació**: {nombre_tasques} tasques * €{cost_per_tasca_job:.4f} = **€{cost_total_job:.4f}**
            """)
        st.metric(label="**Cost per tasca**", value=f"€{cost_per_tasca_job:.4f}")
        st.metric(label="**Cost total**", value=f"€{cost_total_job:.4f}")
        st.metric(label="**Temps Total Actiu**", value=f"{temps_total_min_job} minuts")
    
    with col2:
        st.header("📉 Resultats All-Purpose Cluster")
        with st.expander("📋 Detalls de l'All-Purpose Cluster"):
            st.markdown(f"""
            - **Tipus d'Instància del Driver**: {instancia_all_purpose_driver.name}
            - **Tipus d'Instància dels Workers**: {instancia_all_purpose_worker.name}
            - **Nombre de Drivers**: {nodes_all_purpose_driver}
            - **Nombre de Workers**: {nodes_all_purpose_workers}
            - **vCPUs per Driver**: {instancia_all_purpose_driver.vCPUs}
            - **vCPUs per Worker**: {instancia_all_purpose_worker.vCPUs}
            - **DBUs per Driver**: {instancia_all_purpose_driver.DBUs}
            - **DBUs per Worker**: {instancia_all_purpose_worker.DBUs}
            - **RAM per Driver**: {instancia_all_purpose_driver.RAM_GB} GB
            - **RAM per Worker**: {instancia_all_purpose_worker.RAM_GB} GB
            - **Nombre màxim de tasques en paral·lel**: {max_parallel_tasks_all_purpose}
            """)
        with st.expander("💰 Càlculs de Cost All-Purpose Cluster"):
            st.markdown(f"""
            **Passos per calcular el cost total en un All-Purpose Cluster:**
            
            1. **Nombre d'Onades**:
                - **Fórmula**: Nombre de Tasques / Nombre màxim de Tasques en Paral·lel
                - **Aplicació**: {nombre_tasques} tasques / {max_parallel_tasks_all_purpose} tasques = {nombre_onades_all_purpose} onades
            
            2. **Temps Total Actiu per Onada**:
                - **Fórmula**: Startup Overhead Time + Temps d'Execució per Tasca
                - **Aplicació**: {startup_overhead_time} minuts + {temps_execucio_per_tasca_min} minuts = {startup_overhead_time + temps_execucio_per_tasca_min} minuts
            
            3. **Temps Total Actiu**:
                - **Fórmula**: Startup Overhead Time + (Nombre d'Onades * Temps d'Execució per Tasca)
                - **Aplicació**: {startup_overhead_time} minuts + ({nombre_onades_all_purpose} onades * {temps_execucio_per_tasca_min} minuts) = **{temps_total_actiu_min_all_purpose} minuts**
            
            4. **Cost de les VM per Onada**:
                - **Fórmula**: ((Startup Overhead Time + Temps d'Execució) / 60) * (Cost Driver + Cost Workers)
                - **Aplicació**: (({startup_overhead_time} + {temps_execucio_per_tasca_min}) / 60) * (€{cost_vm_all_purpose_driver} + €{cost_vm_all_purpose_workers}) = **€{(startup_overhead_time + temps_execucio_per_tasca_min)/60 * (cost_vm_all_purpose_driver + cost_vm_all_purpose_workers):.4f}**
            
            5. **Cost de les DBUs durant l'Execució**:
                - **Fórmula**: (Temps d'Execució per Tasca / 60) * Total DBUs * Cost per DBU-hora 
                - **Aplicació**: ({temps_execucio_per_tasca_min} / 60) * {dbus_all_purpose} DBUs * €{cost_dbu_all_purpose} = **€{(temps_execucio_per_tasca_min / 60) * dbus_all_purpose * cost_dbu_all_purpose:.4f}**
            
            6. **Cost Total per Onada**:
                - **Fórmula**: Cost VM per Onada + Cost DBU Execució
                - **Aplicació**: €{((startup_overhead_time + temps_execucio_per_tasca_min)/60) * (cost_vm_all_purpose_driver + cost_vm_all_purpose_workers):.4f} + €{(temps_execucio_per_tasca_min / 60) * dbus_all_purpose * cost_dbu_all_purpose:.4f} = **€{(((startup_overhead_time + temps_execucio_per_tasca_min)/60) * (cost_vm_all_purpose_driver + cost_vm_all_purpose_workers)) + ((temps_execucio_per_tasca_min / 60) * dbus_all_purpose * cost_dbu_all_purpose):.4f}**
            
            7. **Cost Total de l'All-Purpose Cluster**:
                - **Fórmula**: Nombre d'Onades * Cost Total per Onada
                - **Aplicació**: {nombre_onades_all_purpose} onades * (Cost Total per Onada) = **€{cost_total_all_purpose:.4f}**
            """)
        st.metric(label="**Cost total**", value=f"€{cost_total_all_purpose:.4f}")
        st.metric(label="**Temps Total Actiu**", value=f"{temps_total_actiu_min_all_purpose} minuts")
    
    # -------------------------------
    # Graphical Comparison of Costs
    st.header("📊 Comparació de Costos")
    data_cost = pd.DataFrame({
        'Clúster': ['Job Cluster', 'All-Purpose Cluster'],
        'Cost Total (€)': [cost_total_job, cost_total_all_purpose]
    })
    
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
    
    # Graphical Comparison of Execution Times
    st.header("⏰ Comparació de Temps d'Execució")
    data_time = pd.DataFrame({
        'Clúster': ['Job Cluster', 'All-Purpose Cluster'],
        'Temps Total Actiu (minuts)': [temps_total_min_job, temps_total_actiu_min_all_purpose]
    })
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
    
    # Scatter plot: Cost vs Time
    st.header("📈 Optimalitat en Temps vs Cost")
    data_optimal = pd.DataFrame({
        'Clúster': ['Job Cluster', 'All-Purpose Cluster'],
        'Cost Total (€)': [cost_total_job, cost_total_all_purpose],
        'Temps Total Actiu (minuts)': [temps_total_min_job, temps_total_actiu_min_all_purpose]
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
    st.write(f"**Cost total Job Cluster:** €{cost_total_job:.4f}")
    st.write(f"**Cost total All-Purpose:** €{cost_total_all_purpose:.4f}")
    st.write(f"**Temps total actiu Job Cluster:** {temps_total_min_job} minuts")
    st.write(f"**Temps total actiu All-Purpose Cluster:** {temps_total_actiu_min_all_purpose} minuts")
    
    diferencia_cost = abs(cost_total_job - cost_total_all_purpose)
    if cost_total_job < cost_total_all_purpose:
        estalvi = diferencia_cost
        percentatge_estalvi = (diferencia_cost / cost_total_all_purpose) * 100
        st.success(f"La opció més econòmica és **Job Cluster**")
        st.write(f"**Estalvi en Cost:** €{estalvi:.4f}")
        st.write(f"**Percentatge d'estalvi en Cost:** {percentatge_estalvi:.2f}%")
    else:
        estalvi = diferencia_cost
        percentatge_estalvi = (diferencia_cost / cost_total_job) * 100
        st.success(f"La opció més econòmica és **All-Purpose Cluster**")
        st.write(f"**Estalvi en Cost:** €{estalvi:.4f}")
        st.write(f"**Percentatge d'estalvi en Cost:** {percentatge_estalvi:.2f}%")
    
    st.markdown("---")
    st.markdown("""
    📝 **Nota**: Aquests càlculs són aproximacions i poden variar segons la naturalesa específica de les tasques, la configuració del clúster i altres factors operatius.
    """)

if __name__ == "__main__":
    main()
