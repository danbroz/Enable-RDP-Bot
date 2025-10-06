# Enable RDP Bot - Architecture Documentation

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Enable RDP Bot                     │
│                   Command-Line Tool                    │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Azure     │  │   OpenAI    │  │   CLI       │    │
│  │   SDK       │  │   API       │  │ Interface   │    │
│  │             │  │             │  │             │    │
│  │ • Compute   │  │ • GPT-4     │  │ • argparse  │    │
│  │ • Network   │  │ • Analysis  │  │ • logging   │    │
│  │ • Resource  │  │ • JSON      │  │ • output    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   VM        │  │   Network   │  │   AI        │    │
│  │ Inspector   │  │   Analysis  │  │ Analysis    │    │
│  │             │  │             │  │             │    │
│  │ • Status    │  │ • NSG Rules │  │ • Root Cause│    │
│  │ • Power     │  │ • Port 3389 │  │ • Fix Steps │    │
│  │ • Config    │  │ • Security  │  │ • Priority  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

## 🔧 Component Architecture

### 1. Azure SDK Integration Layer

**Purpose**: Interface with Azure services for VM and network management

**Components**:
- `ComputeManagementClient`: VM status, power state, configuration
- `NetworkManagementClient`: NSG rules, network interfaces
- `ResourceManagementClient`: Resource group and subscription management
- `DefaultAzureCredential`: Secure authentication via Azure CLI

**Key Operations**:
```python
# VM Status Retrieval
vm = compute_client.virtual_machines.get(resource_group, vm_name)
instance_view = compute_client.virtual_machines.instance_view(resource_group, vm_name)

# Network Security Group Analysis
nsg = network_client.network_security_groups.get(resource_group, nsg_name)
for rule in nsg.security_rules:
    if rule.destination_port_range == '3389':
        # Analyze RDP access rules
```

### 2. OpenAI API Integration Layer

**Purpose**: AI-powered analysis and recommendations

**Components**:
- `OpenAI Client`: GPT-4 model integration
- `Prompt Engineering`: Structured prompts for RDP troubleshooting
- `Response Parsing`: JSON response validation and processing

**Key Operations**:
```python
# AI Analysis
response = openai_client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are an expert Azure RDP troubleshooting specialist."},
        {"role": "user", "content": f"Analyze: {context}"}
    ],
    temperature=0.3,
    max_tokens=1000
)
```

### 3. CLI Interface Layer

**Purpose**: User interaction and command processing

**Components**:
- `argparse`: Command-line argument parsing
- `logging`: Structured logging and output
- `JSON Output`: Machine-readable results

**Key Operations**:
```python
# Command Line Interface
parser.add_argument('--resource-group', required=True)
parser.add_argument('--vm', required=True)
parser.add_argument('--auto-fix', action='store_true')
parser.add_argument('--verbose', action='store_true')
```

## 🔄 Data Flow Architecture

### 1. Authentication Flow
```
User → Azure CLI Login → DefaultAzureCredential → Azure SDK Clients
```

### 2. Diagnostic Flow
```
CLI Input → VM Status Check → Network Analysis → AI Analysis → JSON Output
```

### 3. Error Handling Flow
```
Exception → Logging → User Notification → Graceful Exit
```

## 🛡️ Security Architecture

### Authentication & Authorization
- **Azure CLI Authentication**: No hardcoded credentials
- **Environment Variables**: Secure API key storage
- **RBAC Integration**: Azure role-based access control
- **Least Privilege**: Minimal required permissions

### Data Protection
- **No Data Persistence**: All data processed in memory
- **Secure Logging**: Sensitive data excluded from logs
- **API Key Protection**: Environment variable isolation
- **Input Validation**: Sanitized user inputs

## 📊 Observability Architecture

### Logging Strategy
```
Application Logs → Console Output + File Logging → JSON Output
```

### Metrics Collection
- **Performance Metrics**: Response times, API calls
- **Error Metrics**: Failure rates, error types
- **Usage Metrics**: Command frequency, success rates

### Monitoring Points
- Azure API call latency
- OpenAI API response time
- Overall troubleshooting duration
- Error occurrence frequency

## 🔧 Runtime Architecture

### Execution Environment
- **Python 3.9+**: Runtime environment
- **Azure CLI**: Authentication provider
- **OpenAI API**: AI analysis service
- **Local File System**: Logging and output

### Dependencies
```
Core Dependencies:
├── openai>=1.3.0 (AI Analysis)
├── azure-identity>=1.15.0 (Authentication)
├── azure-mgmt-compute>=29.5.0 (VM Management)
├── azure-mgmt-network>=23.1.0 (Network Analysis)
├── azure-mgmt-resource>=23.0.1 (Resource Management)
├── python-dotenv>=1.0.0 (Environment Variables)
└── requests>=2.31.0 (HTTP Client)
```

## 🚀 Scalability Architecture

### Horizontal Scaling
- **Stateless Design**: No shared state between executions
- **Independent Operations**: Each run is isolated
- **Resource Pooling**: Azure SDK connection reuse

### Vertical Scaling
- **Memory Efficient**: Minimal memory footprint
- **CPU Optimized**: Async operations where possible
- **Network Optimized**: Efficient API call patterns

## 🔄 Extensibility Architecture

### Plugin Architecture
```python
class TroubleshootingPlugin:
    def diagnose(self, context: Dict) -> Dict:
        pass
    
    def fix(self, context: Dict) -> Dict:
        pass
```

### Configuration Management
- **Environment Variables**: Runtime configuration
- **Command Line Options**: User preferences
- **Default Values**: Sensible defaults

## 📈 Performance Architecture

### Optimization Strategies
- **Connection Reuse**: Azure SDK client reuse
- **Parallel Operations**: Concurrent API calls where possible
- **Caching**: Azure resource metadata caching
- **Lazy Loading**: On-demand resource retrieval

### Performance Targets
- **VM Status Check**: < 2 seconds
- **Network Analysis**: < 3 seconds
- **AI Analysis**: < 5 seconds
- **Total Execution**: < 10 seconds

## 🔧 Deployment Architecture

### Local Deployment
```
Developer Machine:
├── Python Environment
├── Azure CLI
├── OpenAI API Key
└── Enable RDP Bot
```

### Production Considerations
- **Container Support**: Docker compatibility
- **CI/CD Integration**: Automated testing
- **Monitoring Integration**: Application insights
- **Security Scanning**: Vulnerability assessment

## 📋 Architecture Benefits

### Simplicity
- **Single Purpose**: Focused on RDP troubleshooting
- **Minimal Dependencies**: Only essential libraries
- **Clear Structure**: Easy to understand and maintain

### Reliability
- **Error Handling**: Comprehensive exception management
- **Retry Logic**: Automatic retry for transient failures
- **Graceful Degradation**: Partial results when possible

### Security
- **No Secrets**: No hardcoded credentials
- **Input Validation**: Sanitized user inputs
- **Audit Trail**: Complete operation logging

### Maintainability
- **Modular Design**: Clear separation of concerns
- **Documentation**: Comprehensive code documentation
- **Testing**: Unit and integration test support
