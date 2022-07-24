"""Main python file_key for adding resources to the application stack."""
from typing import Dict, Any
from aws_cdk import (
    core,
    aws_sns as sns,
    aws_kms as kms,
    aws_lambda 
)
from constructs import Construct
from .iam_construct import IAMConstruct
from .kms_construct import KMSConstruct
from .sns_construct import SNSConstruct
from .lambda_construct import LambdaConstruct
from .s3_construct import S3Construct
from .glue_construct import GlueConstruct
from .stepfunction_construct import StepFunctionConstruct

class CdkGlueDbTableInfraStack(core.Stack):
    """Build the app stacks and its resources."""
    def __init__(self, env_var: str, scope: core.Construct, 
                 app_id: str, config: dict, **kwargs: Dict[str, Any]) -> None:
        """Creates the cloudformation templates for the projects."""
        super().__init__(scope, app_id, **kwargs)
        self.env_var = env_var
        self.config = config
        CdkGlueDbTableInfraStack.create_stack(self, self.env_var, config=config)
        
    @staticmethod
    def create_stack(stack: core.Stack, env: str, config: dict) -> None:
        """Create and add the resources to the application stack"""
        
        # KMS infra setup
        kms_pol_doc = IAMConstruct.get_kms_policy_document()
        
        kms_key = KMSConstruct.create_kms_key(
            stack=stack,
            config=config,
            env=env,
            policy_doc=kms_pol_doc
        )
        
        # SNS infra setup
        sns_topic = CdkGlueDbTableInfraStack.setup_sns_topic(config, env, stack)
        
        # Actuals Lambda Infra Setup
        actuals_lambda = CdkGlueDbTableInfraStack.create_actuals_lambda_functions(
            stack=stack,
            config=config,
            env=env,
            kms_key=kms_key,
            sns_topic=sns_topic
        )
        
        # Actuals Step Function Infra
        CdkGlueDbTableInfraStack.create_actuals_step_function(
            stack=stack,
            config=config,
            env=env,
            sns_topic=sns_topic,
            state_machine_name=f"{config['global']['app-name']}-actuals-stateMachine",
            actuals_lambda=actuals_lambda
        )
        
    
    @staticmethod
    def setup_sns_topic(
        config: dict,
        env: str,
        stack: core.Stack) -> sns.Topic:
        """Setup the SNS topic and returns an SNS Topic Object"""
        sns_topic = SNSConstruct.create_sns_topic(
            stack=stack,
            env=env,
            config=config
        )
        SNSConstruct.subscribe_email(env=env, config=config, topic=sns_topic)
        return sns_topic
    
    @staticmethod
    def create_actuals_lambda_functions(
        stack: core.Stack,
        config: dict,
        env: str,
        kms_key: kms.Key,
        sns_topic: sns.Topic) -> Dict[str, aws_lambda.Function]:
        """Create placeholder lambda function and roles."""
        actuals_lambda = {}
        
        # Update table and partition lambda -------------------------------------
        act_update_table_policy = IAMConstruct.create_managed_policy(
            stack=stack,
            env=env,
            config=config,
            policy_name="act_update_table",
            statements=[
                LambdaConstruct.get_cloudwatch_policy(
                    config['global']['act_update_table_lambdaLogsArn']
                ),
                S3Construct.get_s3_object_policy(config['global']['bucket_arn']),
                GlueConstruct.get_glue_policy(config, env),
                KMSConstruct.get_kms_key_encrypt_decrypt_policy([kms_key.key_arn]),
                SNSConstruct.get_sns_publish_policy(sns_topic.topic_arn)
            ]
        )
        
        act_update_table_role = IAMConstruct.create_role(
            stack=stack,
            env=env,
            config=config,
            role_name="act_update_table",
            assumed_by=["lambda"]   
        )
        
        act_update_table_role.add_managed_policy(act_update_table_policy)
        
        actuals_lambda["act_update_table_lambda"] = LambdaConstruct.create_lambda(
            stack=stack,
            env=env,
            config=config,
            lambda_name="act_update_table_lambda",
            role=act_update_table_role,
            duration=core.Duration.minutes(15)
        )
        
        return actuals_lambda
    
    
    @staticmethod
    def create_actuals_step_function(
        stack: core.Stack,
        config: dict,
        env: str,
        sns_topic,
        state_machine_name: str,
        actuals_lambda: Dict[
                            str, aws_lambda.Function]) -> None:
        """Create Step Function and necessary IAM role with input lambdas."""
        
        state_machine_policy = IAMConstruct.create_managed_policy(
            stack=stack,
            env=env,
            config=config,
            policy_name="actStateMachine",
            statements=[
                StepFunctionConstruct.get_sfn_lambda_invoke_job_policy_statement(
                    config=config,
                    env=env
                ),
                SNSConstruct.get_sns_publish_policy(sns_topic.topic_arn)
            ]
        )
        
        state_machine_role = IAMConstruct.create_role(
            stack=stack,
            env=env,
            config=config,
            role_name="actStateMachine",
            assumed_by=['states']
        )
        state_machine_role.add_managed_policy(state_machine_policy)
        
        StepFunctionConstruct.create_actuals_step_function(
            stack=stack,
            env=env,
            config=config,
            role=state_machine_role,
            sns_topic=sns_topic,
            state_machine_name=state_machine_name,
            act_update_table=actuals_lambda["act_update_table_lambda"]
        )
        