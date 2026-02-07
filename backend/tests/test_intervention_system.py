"""
Tests for the Intervention System components
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta

from app.services.intervention_service import InterventionSystem, StepContext
from app.schemas import HelpMessage


class TestInterventionSystem:
    """Test the InterventionSystem service"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.intervention_system = InterventionSystem()
        
    def test_should_intervene_low_score(self):
        """Test intervention triggering for low engagement score"""
        # Test score below threshold
        assert self.intervention_system._should_intervene(1, 25.0) == True
        
        # Test score at threshold
        assert self.intervention_system._should_intervene(1, 30.0) == False
        
        # Test score above threshold
        assert self.intervention_system._should_intervene(1, 45.0) == False
        
    def test_should_intervene_deduplication(self):
        """Test intervention deduplication logic"""
        user_id = 1
        
        # First intervention should be allowed
        assert self.intervention_system._should_intervene(user_id, 25.0) == True
        
        # Set last intervention timestamp
        self.intervention_system.last_interventions[user_id] = datetime.utcnow()
        
        # Second intervention within window should be blocked
        assert self.intervention_system._should_intervene(user_id, 25.0) == False
        
        # Intervention after window should be allowed
        self.intervention_system.last_interventions[user_id] = datetime.utcnow() - timedelta(minutes=6)
        assert self.intervention_system._should_intervene(user_id, 25.0) == True
        
    def test_generate_step_title(self):
        """Test step title generation for different roles"""
        # Test Developer role
        assert self.intervention_system._generate_step_title("Developer", 1) == "API Authentication Setup"
        assert self.intervention_system._generate_step_title("Developer", 2) == "Making Your First API Call"
        
        # Test Business_User role
        assert self.intervention_system._generate_step_title("Business_User", 1) == "Understanding the Platform"
        assert self.intervention_system._generate_step_title("Business_User", 2) == "Creating Your First Workflow"
        
        # Test Admin role
        assert self.intervention_system._generate_step_title("Admin", 1) == "System Configuration"
        
        # Test unknown role
        assert self.intervention_system._generate_step_title("Unknown", 1) == "Getting Started"
        
        # Test step number beyond available steps
        assert self.intervention_system._generate_step_title("Developer", 10) == "Step 10"
        
    def test_get_help_content_for_context(self):
        """Test contextual help content generation"""
        context = StepContext(
            step_number=1,
            total_steps=5,
            step_title="API Authentication Setup",
            user_role="Developer",
            time_on_step=120,  # 2 minutes
            previous_interventions=0,
            engagement_score=25.0
        )
        
        content = self.intervention_system._get_help_content_for_context(context)
        
        # Should contain role-specific help
        assert "API authentication" in content
        assert "API key" in content
        
        # Test with long time on step
        context.time_on_step = 400  # More than 5 minutes
        content = self.intervention_system._get_help_content_for_context(context)
        assert "while" in content  # Should mention time spent
        
        # Test with previous interventions
        context.previous_interventions = 1
        content = self.intervention_system._get_help_content_for_context(context)
        assert "extra support" in content  # Should mention additional support
        
    async def test_generate_contextual_help(self):
        """Test help message generation"""
        context = StepContext(
            step_number=2,
            total_steps=5,
            step_title="Making Your First API Call",
            user_role="Developer",
            time_on_step=180,
            previous_interventions=0,
            engagement_score=20.0
        )
        
        help_message = await self.intervention_system._generate_contextual_help(context)
        
        # Verify help message structure
        assert isinstance(help_message, HelpMessage)
        assert help_message.message_id is not None
        assert help_message.content is not None
        assert help_message.message_type == "contextual_help"
        assert help_message.dismissible == True
        
        # Verify context is included
        assert help_message.context["step_number"] == 2
        assert help_message.context["step_title"] == "Making Your First API Call"
        assert help_message.context["user_role"] == "Developer"
        assert help_message.context["engagement_score"] == 20.0
        
    def test_intervention_threshold_configuration(self):
        """Test intervention threshold configuration"""
        # Default threshold
        assert self.intervention_system.intervention_threshold == 30.0
        
        # Update threshold
        self.intervention_system.intervention_threshold = 25.0
        assert self.intervention_system.intervention_threshold == 25.0
        
        # Test with new threshold
        assert self.intervention_system._should_intervene(1, 26.0) == False
        assert self.intervention_system._should_intervene(1, 24.0) == True
        
    def test_deduplication_window_configuration(self):
        """Test deduplication window configuration"""
        # Default window
        assert self.intervention_system.deduplication_window_minutes == 5
        
        # Update window
        self.intervention_system.deduplication_window_minutes = 10
        assert self.intervention_system.deduplication_window_minutes == 10
        
        # Test with new window
        user_id = 1
        self.intervention_system.last_interventions[user_id] = datetime.utcnow() - timedelta(minutes=8)
        
        # Should still be blocked with 10-minute window
        assert self.intervention_system._should_intervene(user_id, 25.0) == False
        
        # Should be allowed after 10+ minutes
        self.intervention_system.last_interventions[user_id] = datetime.utcnow() - timedelta(minutes=11)
        assert self.intervention_system._should_intervene(user_id, 25.0) == True


class TestHelpMessageGeneration:
    """Test help message generation for different scenarios"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.intervention_system = InterventionSystem()
        
    def test_developer_help_messages(self):
        """Test help messages for Developer role"""
        for step in range(1, 6):
            context = StepContext(
                step_number=step,
                total_steps=5,
                step_title=self.intervention_system._generate_step_title("Developer", step),
                user_role="Developer",
                time_on_step=120,
                previous_interventions=0,
                engagement_score=25.0
            )
            
            content = self.intervention_system._get_help_content_for_context(context)
            assert content is not None
            assert len(content) > 0
            
    def test_business_user_help_messages(self):
        """Test help messages for Business_User role"""
        for step in range(1, 4):
            context = StepContext(
                step_number=step,
                total_steps=3,
                step_title=self.intervention_system._generate_step_title("Business_User", step),
                user_role="Business_User",
                time_on_step=120,
                previous_interventions=0,
                engagement_score=25.0
            )
            
            content = self.intervention_system._get_help_content_for_context(context)
            assert content is not None
            assert len(content) > 0
            
    def test_admin_help_messages(self):
        """Test help messages for Admin role"""
        for step in range(1, 5):
            context = StepContext(
                step_number=step,
                total_steps=4,
                step_title=self.intervention_system._generate_step_title("Admin", step),
                user_role="Admin",
                time_on_step=120,
                previous_interventions=0,
                engagement_score=25.0
            )
            
            content = self.intervention_system._get_help_content_for_context(context)
            assert content is not None
            assert len(content) > 0


if __name__ == "__main__":
    # Run basic tests
    test_system = TestInterventionSystem()
    test_system.setup_method()
    
    print("Testing intervention threshold logic...")
    test_system.test_should_intervene_low_score()
    print("✓ Threshold logic works correctly")
    
    print("Testing deduplication logic...")
    test_system.test_should_intervene_deduplication()
    print("✓ Deduplication logic works correctly")
    
    print("Testing step title generation...")
    test_system.test_generate_step_title()
    print("✓ Step title generation works correctly")
    
    print("Testing help content generation...")
    test_system.test_get_help_content_for_context()
    print("✓ Help content generation works correctly")
    
    print("\nAll intervention system tests passed! ✅")