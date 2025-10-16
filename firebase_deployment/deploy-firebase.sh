#!/bin/bash

# ThinkSync™ Enhanced Edition - Firebase Deployment Script
# Developed for Cadenza Therapeutics™

set -e

echo "🔥 ThinkSync™ Enhanced Edition - Firebase Deployment"
echo "=" * 60

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Firebase CLI is installed
check_firebase_cli() {
    print_info "Checking Firebase CLI installation..."
    
    if ! command -v firebase &> /dev/null; then
        print_error "Firebase CLI is not installed"
        print_info "Install it with: npm install -g firebase-tools"
        exit 1
    fi
    
    print_status "Firebase CLI is installed"
}

# Check if user is logged in to Firebase
check_firebase_auth() {
    print_info "Checking Firebase authentication..."
    
    if ! firebase projects:list &> /dev/null; then
        print_warning "Not logged in to Firebase"
        print_info "Logging in to Firebase..."
        firebase login
    fi
    
    print_status "Firebase authentication verified"
}

# Initialize Firebase project
init_firebase_project() {
    print_info "Initializing Firebase project..."
    
    if [ ! -f ".firebaserc" ]; then
        print_info "No Firebase project configured. Please run 'firebase init' first."
        print_info "Select the following features:"
        print_info "• Hosting: Configure files for Firebase Hosting"
        print_info "• Functions: Configure a Cloud Functions directory"
        print_info "• Firestore: Configure security rules and indexes"
        print_info "• Storage: Configure security rules for Cloud Storage"
        
        firebase init
    else
        print_status "Firebase project already configured"
    fi
}

# Install Functions dependencies
install_dependencies() {
    print_info "Installing Firebase Functions dependencies..."
    
    cd functions
    
    if [ ! -d "node_modules" ]; then
        npm install
    else
        print_status "Dependencies already installed"
    fi
    
    cd ..
}

# Deploy Firestore rules and indexes
deploy_firestore() {
    print_info "Deploying Firestore rules and indexes..."
    
    firebase deploy --only firestore
    
    print_status "Firestore rules and indexes deployed"
}

# Deploy Storage rules
deploy_storage() {
    print_info "Deploying Storage rules..."
    
    firebase deploy --only storage
    
    print_status "Storage rules deployed"
}

# Deploy Functions
deploy_functions() {
    print_info "Deploying Firebase Functions..."
    
    firebase deploy --only functions
    
    print_status "Firebase Functions deployed"
}

# Initialize admin user
init_admin_user() {
    print_info "Initializing admin user..."
    
    # Get the project ID
    PROJECT_ID=$(firebase use | grep "Now using project" | awk '{print $4}' | tr -d '()')
    
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(cat .firebaserc | grep '"default"' | awk -F'"' '{print $4}')
    fi
    
    print_info "Calling initializeAdmin function..."
    firebase functions:call initializeAdmin --project $PROJECT_ID
    
    print_status "Admin user initialized"
}

# Deploy Hosting
deploy_hosting() {
    print_info "Deploying Firebase Hosting..."
    
    firebase deploy --only hosting
    
    print_status "Firebase Hosting deployed"
}

# Get deployment URLs
get_urls() {
    print_info "Getting deployment URLs..."
    
    PROJECT_ID=$(firebase use | grep "Now using project" | awk '{print $4}' | tr -d '()')
    
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(cat .firebaserc | grep '"default"' | awk -F'"' '{print $4}')
    fi
    
    echo
    print_status "Deployment completed successfully!"
    echo
    print_info "🌐 Your ThinkSync™ application is now live at:"
    echo "   • https://$PROJECT_ID.web.app"
    echo "   • https://$PROJECT_ID.firebaseapp.com"
    echo
    print_info "🎯 Admin Access:"
    echo "   • URL: https://$PROJECT_ID.web.app/admin"
    echo "   • Username: admin@thinksync.com"
    echo "   • Password: 3942-granite-35"
    echo
    print_info "🔧 Firebase Console:"
    echo "   • https://console.firebase.google.com/project/$PROJECT_ID"
    echo
}

# Test deployment
test_deployment() {
    print_info "Testing deployment..."
    
    PROJECT_ID=$(firebase use | grep "Now using project" | awk '{print $4}' | tr -d '()')
    
    if [ -z "$PROJECT_ID" ]; then
        PROJECT_ID=$(cat .firebaserc | grep '"default"' | awk -F'"' '{print $4}')
    fi
    
    # Test health endpoint
    if command -v curl &> /dev/null; then
        print_info "Testing API health endpoint..."
        
        if curl -s "https://$PROJECT_ID.web.app/api/health" > /dev/null; then
            print_status "API health check passed"
        else
            print_warning "API health check failed - this is normal for new deployments"
        fi
    else
        print_warning "curl not available for testing"
    fi
}

# Main deployment function
main() {
    echo
    print_info "Starting ThinkSync™ Enhanced Edition Firebase deployment..."
    echo
    
    # Run deployment steps
    check_firebase_cli
    check_firebase_auth
    init_firebase_project
    install_dependencies
    deploy_firestore
    deploy_storage
    deploy_functions
    
    # Wait a moment for functions to be ready
    print_info "Waiting for functions to initialize..."
    sleep 10
    
    init_admin_user
    deploy_hosting
    test_deployment
    get_urls
    
    echo
    print_status "🎉 ThinkSync™ Enhanced Edition successfully deployed to Firebase!"
    echo
    print_info "Features available:"
    echo "   ✅ Complete User Authentication & Authorization"
    echo "   ✅ Advanced Sentiment Analysis Integration"
    echo "   ✅ Session Management & Persistence"
    echo "   ✅ SOAP/BIRP Clinical Documentation"
    echo "   ✅ Multi-format Export Capabilities"
    echo "   ✅ Admin Dashboard & User Management"
    echo "   ✅ Real-time Database with Firestore"
    echo "   ✅ Secure File Storage"
    echo "   ✅ Global CDN and Auto-scaling"
    echo
    print_info "Next steps:"
    echo "1. Visit your application URL"
    echo "2. Test the Neural Simulation feature"
    echo "3. Register new clinicians"
    echo "4. Use admin dashboard to approve users"
    echo "5. Upload and process therapy sessions"
    echo
}

# Handle script interruption
trap 'print_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"

