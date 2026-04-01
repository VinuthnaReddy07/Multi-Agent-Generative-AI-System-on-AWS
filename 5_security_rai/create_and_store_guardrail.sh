#!/bin/bash

# Complete Guardrail Creation and Parameter Store Integration Script
# This script creates a guardrail, configures it, and automatically stores the configuration in Parameter Store

set -e  # Exit on any error

# Color codes for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo
    echo "=================================================================="
    echo "CREATING GUARDRAIL AND STORING CONFIGURATION"
    echo "=================================================================="
}

print_section() {
    local title=$1
    echo
    echo "--- $title ---"
}

print_footer() {
    echo "=================================================================="
    echo
}

# Function to create guardrail configuration files
create_config_files() {
    print_section "Creating Configuration Files"
    
    # Content filtering configuration
    cat > content-config.json << 'EOF'
{
  "filtersConfig": [
    {
      "type": "HATE",
      "inputStrength": "MEDIUM",
      "outputStrength": "MEDIUM"
    },
    {
      "type": "INSULTS",
      "inputStrength": "MEDIUM",
      "outputStrength": "MEDIUM"
    },
    {
      "type": "SEXUAL",
      "inputStrength": "HIGH",
      "outputStrength": "HIGH"
    },
    {
      "type": "VIOLENCE",
      "inputStrength": "HIGH",
      "outputStrength": "HIGH"
    },
    {
      "type": "MISCONDUCT",
      "inputStrength": "MEDIUM",
      "outputStrength": "MEDIUM"
    }
  ]
}
EOF

    # Topic boundaries configuration
    cat > topic-config.json << 'EOF'
{
  "topicsConfig": [
    {
      "name": "Personal Information Requests",
      "definition": "Requests for personal information about customers or employees",
      "examples": [
        "What is the customer database?",
        "Give me employee personal information",
        "What are customer credit card details?"
      ],
      "type": "DENY"
    }
  ]
}
EOF

    # Word filtering configuration
    cat > word-config.json << 'EOF'
{
  "managedWordListsConfig": [
    {
      "type": "PROFANITY"
    }
  ],
  "wordsConfig": [
    {
      "text": "hack"
    },
    {
      "text": "exploit"
    },
    {
      "text": "bypass"
    },
    {
      "text": "jailbreak"
    }
  ]
}
EOF

    # PII configuration
    cat > pii-config.json << 'EOF'
{
  "piiEntitiesConfig": [
    {
      "type": "EMAIL",
      "action": "ANONYMIZE"
    },
    {
      "type": "PHONE",
      "action": "ANONYMIZE"
    },
    {
      "type": "ADDRESS",
      "action": "ANONYMIZE"
    },
    {
      "type": "CREDIT_DEBIT_CARD_NUMBER",
      "action": "BLOCK"
    },
    {
      "type": "US_SOCIAL_SECURITY_NUMBER",
      "action": "BLOCK"
    },
    {
      "type": "NAME",
      "action": "ANONYMIZE"
    }
  ],
  "regexesConfig": [
    {
      "name": "Employee ID",
      "pattern": "EMP-[0-9]{6}",
      "action": "ANONYMIZE",
      "description": "Employee identification numbers"
    },
    {
      "name": "Order Number",
      "pattern": "ORD-[0-9]{8}",
      "action": "ANONYMIZE",
      "description": "Customer order numbers"
    }
  ]
}
EOF

    print_status $GREEN "✓ Configuration files created"
}

# Function to create the guardrail
create_guardrail() {
    print_section "Creating Guardrail"
    
    # Create initial guardrail
    GUARDRAIL_ID=$(aws bedrock create-guardrail \
      --name "P2PWorkshopGuardrail" \
      --description "Security guardrail for P2P Workshop Bedrock Agent" \
      --blocked-input-messaging "I cannot process that request due to content policies. Please try a different question." \
      --blocked-outputs-messaging "I cannot provide that information due to content policies." \
      --content-policy-config file://content-config.json \
      --query 'guardrailId' \
      --output text)
    
    if [ -z "$GUARDRAIL_ID" ]; then
        print_status $RED "✗ Failed to create guardrail"
        exit 1
    fi
    
    print_status $GREEN "✓ Created guardrail: $GUARDRAIL_ID"
    
    # Update with topic boundaries
    print_status $BLUE "Adding topic boundaries..."
    aws bedrock update-guardrail \
      --guardrail-identifier $GUARDRAIL_ID \
      --name "P2PWorkshopGuardrail" \
      --description "Security guardrail for P2P Workshop Bedrock Agent" \
      --blocked-input-messaging "I cannot process that request due to content policies. Please try a different question." \
      --blocked-outputs-messaging "I cannot provide that information due to content policies." \
      --content-policy-config file://content-config.json \
      --topic-policy-config file://topic-config.json > /dev/null
    
    print_status $GREEN "✓ Topic boundaries configured"
    
    # Update with word filtering
    print_status $BLUE "Adding word filtering..."
    aws bedrock update-guardrail \
      --guardrail-identifier $GUARDRAIL_ID \
      --name "P2PWorkshopGuardrail" \
      --description "Security guardrail for P2P Workshop Bedrock Agent" \
      --blocked-input-messaging "I cannot process that request due to content policies. Please try a different question." \
      --blocked-outputs-messaging "I cannot provide that information due to content policies." \
      --content-policy-config file://content-config.json \
      --topic-policy-config file://topic-config.json \
      --word-policy-config file://word-config.json > /dev/null
    
    print_status $GREEN "✓ Word filtering configured"
    
    # Update with PII handling
    print_status $BLUE "Adding sensitive information handling..."
    aws bedrock update-guardrail \
      --guardrail-identifier $GUARDRAIL_ID \
      --name "P2PWorkshopGuardrail" \
      --description "Security guardrail for P2P Workshop Bedrock Agent" \
      --blocked-input-messaging "I cannot process that request due to content policies. Please try a different question." \
      --blocked-outputs-messaging "I cannot provide that information due to content policies." \
      --content-policy-config file://content-config.json \
      --topic-policy-config file://topic-config.json \
      --word-policy-config file://word-config.json \
      --sensitive-information-policy-config file://pii-config.json > /dev/null
    
    print_status $GREEN "✓ Sensitive information handling configured"
    
    # Create guardrail version
    print_status $BLUE "Creating guardrail version..."
    GUARDRAIL_VERSION=$(aws bedrock create-guardrail-version \
      --guardrail-identifier $GUARDRAIL_ID \
      --query 'version' \
      --output text)
    
    if [ -z "$GUARDRAIL_VERSION" ]; then
        print_status $RED "✗ Failed to create guardrail version"
        exit 1
    fi
    
    print_status $GREEN "✓ Created guardrail version: $GUARDRAIL_VERSION"
    
    # Export variables for Parameter Store storage
    print_status $GREEN "✓ Adding Guardrail ID and Version to env.sh"
    echo "export GUARDRAIL_ID=\"$GUARDRAIL_ID\"" | tee -a ~/environment/env.sh
    echo "export GUARDRAIL_VERSION=\"$GUARDRAIL_VERSION\"" | tee -a ~/environment/env.sh
    print_status $GREEN "✓ Added GUARDRAIL_ID=$GUARDRAIL_ID and GUARDRAIL_VERSION=$GUARDRAIL_VERSION to env.sh"
}

# Function to store configuration in Parameter Store
store_configuration() {
    print_section "Storing Configuration in Parameter Store"
    
    local script_dir="$(dirname "$0")"
    local python_script="$script_dir/parameter_store_manager.py"
    
    if [ -f "$python_script" ]; then
        print_status $BLUE "Using Parameter Store manager script..."
        if python3 "$python_script" "$GUARDRAIL_ID" "$GUARDRAIL_VERSION" "true"; then
            print_status $GREEN "✓ Configuration stored successfully using Python script"
        else
            print_status $RED "✗ Failed to store configuration using Python script"
            return 1
        fi
    else
        print_status $YELLOW "Python script not found, using AWS CLI method..."
        
        local timestamp=$(date -u +%Y-%m-%dT%H:%M:%SZ)
        
        # Store parameters using AWS CLI
        aws ssm put-parameter \
          --name "/p2p-workshop/guardrail/id" \
          --value "$GUARDRAIL_ID" \
          --type "String" \
          --description "Bedrock Guardrail identifier for P2P Workshop" \
          --overwrite > /dev/null
        
        aws ssm put-parameter \
          --name "/p2p-workshop/guardrail/version" \
          --value "$GUARDRAIL_VERSION" \
          --type "String" \
          --description "Guardrail version for P2P Workshop" \
          --overwrite > /dev/null
        
        aws ssm put-parameter \
          --name "/p2p-workshop/guardrail/enabled" \
          --value "true" \
          --type "String" \
          --description "Enable/disable guardrails for P2P Workshop" \
          --overwrite > /dev/null
        
        aws ssm put-parameter \
          --name "/p2p-workshop/guardrail/created" \
          --value "$timestamp" \
          --type "String" \
          --description "Guardrail configuration creation timestamp" \
          --overwrite > /dev/null
        
        print_status $GREEN "✓ Configuration stored using AWS CLI"
    fi
}

# Function to validate stored configuration
validate_configuration() {
    print_section "Validating Stored Configuration"
    
    local script_dir="$(dirname "$0")"
    local validation_script="$script_dir/validate_parameter_store.py"
    
    if [ -f "$validation_script" ]; then
        print_status $BLUE "Using validation script..."
        if python3 "$validation_script"; then
            print_status $GREEN "✓ Configuration validation successful"
        else
            print_status $RED "✗ Configuration validation failed"
            return 1
        fi
    else
        print_status $YELLOW "Validation script not found, using manual validation..."
        
        # Manual validation using AWS CLI
        local params=("/p2p-workshop/guardrail/id" "/p2p-workshop/guardrail/version" "/p2p-workshop/guardrail/enabled" "/p2p-workshop/guardrail/created")
        local validation_success=true
        
        for param in "${params[@]}"; do
            if value=$(aws ssm get-parameter --name "$param" --query 'Parameter.Value' --output text 2>/dev/null); then
                print_status $GREEN "✓ Validated parameter: $param = $value"
            else
                print_status $RED "✗ Failed to retrieve parameter: $param"
                validation_success=false
            fi
        done
        
        if [ "$validation_success" = true ]; then
            print_status $GREEN "✓ Manual validation successful"
        else
            print_status $RED "✗ Manual validation failed"
            return 1
        fi
    fi
}

# Function to display final summary
display_summary() {
    print_section "Configuration Summary"
    
    echo "=================================================================="
    echo "GUARDRAIL CREATION AND STORAGE COMPLETE"
    echo "=================================================================="
    echo "Guardrail ID:      $GUARDRAIL_ID"
    echo "Version:           $GUARDRAIL_VERSION"
    echo "Status:            Enabled"
    echo "Parameter Store:   Configured"
    echo "=================================================================="
    echo "Configuration stored in Parameter Store at:"
    echo "  /p2p-workshop/guardrail/id"
    echo "  /p2p-workshop/guardrail/version"
    echo "  /p2p-workshop/guardrail/enabled"
    echo "  /p2p-workshop/guardrail/created"
    echo "=================================================================="
    echo
    print_status $GREEN "✓ Guardrail creation and Parameter Store integration complete!"
    print_status $BLUE "Your production deployment in Section 6 will automatically load this configuration."
    echo
    echo "Next steps:"
    echo "1. Uncomment the guardrail integration code in barista_supervisor_agent.py"
    echo "2. Test the guardrail functionality with your agent"
    echo "3. Proceed to Section 6 for production deployment"
}

# Function to cleanup temporary files
cleanup() {
    print_status $BLUE "Cleaning up temporary files..."
    rm -f content-config.json topic-config.json word-config.json pii-config.json
    print_status $GREEN "✓ Cleanup complete"
}

# Main execution function
main() {
    print_header
    
    # Execute all steps
    create_config_files
    create_guardrail
    store_configuration
    validate_configuration
    display_summary
    cleanup
    
    print_footer
}

# Handle script interruption
trap 'print_status $RED "\n✗ Script interrupted by user"; cleanup; exit 1' INT

# Execute main function
main "$@"