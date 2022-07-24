"""Code for generating the step resources.
This is for creating the various tasks, retry, error
and states that are involved."""

from email import message
from typing import Dict, Any, List
from aws_cdk import aws_iam as iam
from aws_cdk import aws_sns as sns
from aws_cdk.aws_lambda import Function
from aws_cdk import aws_stepfunctions as sfn
from aws_cdk import aws_stepfunctions_tasks
from aws_cdk.core import Stack, Duration

class StepFunctionConstruct:
    """Class has methods to create a step function."""
    
    @staticmethod
    def create_actuals_step_function(
        stack: Stack,
        env: str,
        config: dict,
        role: iam.Role,
        sns_topic: sns.Topic,
        state_machine_name: str,
        act_update_table: Function
        ) -> sfn.StateMachine:
        """Create Actuals step Function."""
        
        project_id_short = config['global']['source-id-short']
        actuals_red_alert = StepFunctionConstruct.create_actuals_alert_task(
            stack=stack,
            env=env,
            config=config,
            subject=f"[Error-{env}]{project_id_short} Step Function",
            sns_topic=sns_topic
        )
        
        # Actuals Update Table Lambda Task
        act_update_table_task = StepFunctionConstruct.create_lambda_task(
            task_lambda=act_update_table,
            stack=stack,
            task_def="Actuals Update Table Lambda",
            result_key="$.updt_table_creation_output")
        act_update_table_task.add_catch(actuals_red_alert, result_path="$.error")
        
        actuals_fail = StepFunctionConstruct.create_fail_state(stack=stack, config=config, env=env, id_name="actuals")
        actuals_red_alert.next(actuals_fail)
        
        definition = StepFunctionConstruct.create_actuals_step_function_definition(
            stack=stack,
            act_update_table_task=act_update_table_task
        )
        
        state_machine = sfn.StateMachine(
            scope=stack,
            id=f"{config['global']['app-name']}-stateMachine-Id",
            state_machine_name=state_machine_name,
            definition=definition,
            role=role
        )
        
        return state_machine
        
        
    @staticmethod
    def create_actuals_alert_task(
        stack: Stack,
        env: str,
        config: dict,
        subject: str,
        sns_topic: sns.Topic) -> sfn.Task:
        """Create Alert Task."""
        
        error_details = f"PROJECT: {config['global']['source-identifier']}. "\
                        f"COMPONENT ARN: {config['global']['actualsStepFunctionArn']}. "\
                        f"REASON: Refer Step Function Execution Logs for details."
        return sfn.Task(
            scope=stack,
            id="ActualsRedAlert",
            task=aws_stepfunctions_tasks.PublishToTopic(
                topic=sns_topic,
                message=sfn.TaskInput.from_object(
                    StepFunctionConstruct.get_text_message(
                        is_event=True,
                        message=error_details,
                        details="Refer Step Function Execution Logs for details.",
                        event_action="PageCritical",
                        itsm_id="12345",
                        source_system=f"{env}- {config['global']['source-identifier']}",
                        primary_ci=config["global"]["kk-app-inventory-id"]
                    )
                ),
                subject=subject
            ),
            result_path="$.output"
        )
       
       
    @staticmethod
    def create_lambda_task(stack: Stack, task_def: str, task_lambda: Function,
                           result_key: str = '$') -> sfn.Task:
        """Create Lambda Task."""
        lambda_task = sfn.Task(
            scope=stack,
            id=task_def,
            task=aws_stepfunctions_tasks.InvokeFunction(task_lambda),
            result_path=result_key
        )
        return lambda_task
       
       
    @staticmethod
    def get_text_message(
        is_event: bool, message: str, details: str, event_action: str = "",
        itsm_id: str = "", source_system: str = "", primary_ci: str = ""):
        """Create notification message object."""
        return {
            "isEvent": is_event,
            "message": message,
            "details": details,
            "eventAction": event_action,
            "itsmId": itsm_id,
            "sourceSystem": source_system,
            "primaryCI": primary_ci
        }
        
        
    @staticmethod
    def create_actuals_step_function_definition(
        stack: Stack,
        act_update_table_task) -> sfn.Chain:
        """Create Step Function Definition."""
        
        exec_param = {"Execution.$": "$$.Execution.Id"}
        
        actuals_start_state = sfn.Pass(
            scope=stack,
            id="ActualsStartState",
            result_path="$.Execution",
            parameters=exec_param
        )
        actuals_success = sfn.Succeed(
            scope=stack,
            id="Actuals Step Function Execution complete."
        )
        
        definition = sfn.Chain.start(
            state=actuals_start_state
        ).next(
            next=act_update_table_task
        ).next(
            next=actuals_success
        )
        return definition
        
        
        
    @staticmethod
    def create_fail_state(stack: Stack, config: dict, env: str, id_name: str) -> sfn.Fail:
        """Create Fail State."""
        fail = sfn.Fail(
            scope=stack,
            id=f"{config['global']['app-name']}-{id_name}-FailTask-Id",
            cause="An exception was thrown and not handled. Check email.",
            error="$.error"
        )
        return fail
        
    
    @staticmethod
    def get_sfn_lambda_invoke_job_policy_statement(
        config: dict, env: str) -> iam.PolicyStatement:
        """Returns policy statement lambdas used for managing SFN resources and components."""
        policy_statement = iam.PolicyStatement()
        policy_statement.effect = iam.Effect.ALLOW
        policy_statement.add_actions("lambda:InvokeFunction")
        policy_statement.add_resources(config['global']['lambdaFunctionArnBase'])
        return policy_statement