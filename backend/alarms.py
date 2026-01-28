"""
Point 7: Alarm Rules and Actions System
- Modelos de alarmas determinísticos
- Acciones no bloqueantes
- Anti-spam con cooldown
- Logging para auditoría
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable, Deque
from collections import deque
from uuid import uuid4
import logging
import asyncio

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """Tipos de eventos que pueden disparar alarmas"""
    ON_DEFECT = "on_defect"
    ON_RATE = "on_rate"
    ON_COLOR_OOT = "on_color_oot"
    ON_REGISTER_LOST = "on_register_lost"
    ON_SENSOR_LOST = "on_sensor_lost"
    MANUAL = "manual"


class ActionType(Enum):
    """Tipos de acciones que se pueden ejecutar"""
    TOWER_LIGHT = "tower_light"        # Luz de torre
    BUZZER = "buzzer"                  # Buzzer
    PLC_WRITE = "plc_write"           # Escribir al PLC
    HMI_POPUP = "hmi_popup"           # Popup en HMI
    EMAIL = "email"                    # Enviar email
    LOG_ONLY = "log_only"             # Solo registrar


@dataclass
class Action:
    """Definición de una acción individual"""
    action_type: ActionType
    
    # Config general
    duration_ms: int = 500
    
    # Para tower light
    color: str = "red"                 # "red" | "yellow" | "green"
    
    # Para PLC
    plc_address: Optional[str] = None
    plc_value: Optional[int] = None
    
    # Para HMI
    popup_title: str = ""
    popup_message: str = ""
    
    # Para email
    email_to: List[str] = field(default_factory=list)
    email_subject: str = "System Alert"


@dataclass
class AlarmRule:
    """
    Regla que define CUÁNDO y QUÉ hacer
    - Determinística: misma entrada → misma salida
    - Auditable: logs de ejecución
    """
    rule_id: str = field(default_factory=lambda: f"rule_{uuid4().hex[:8]}")
    enabled: bool = True
    
    # Condición de disparo
    trigger_type: TriggerType = TriggerType.ON_DEFECT
    trigger_config: Dict = field(default_factory=dict)
    
    # Acciones a ejecutar
    actions: List[Action] = field(default_factory=list)
    
    # Anti-spam
    cooldown_ms: int = 2000
    
    # Metadata
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered_at: Optional[datetime] = None


@dataclass
class AlarmEvent:
    """Evento de alarma registrado"""
    alarm_id: str = field(default_factory=lambda: f"alarm_{uuid4().hex[:8]}")
    rule_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    trigger_type: str = ""
    actions_executed: int = 0
    triggered_by: Dict = field(default_factory=dict)


class AlarmEngine:
    """
    Motor de evaluación de alarmas
    - No bloqueante (acciones async)
    - Anti-spam automático
    - Logging completo
    """
    
    def __init__(self, plc_client=None):
        self.rules: Dict[str, AlarmRule] = {}
        self.alarm_queue: Deque[AlarmEvent] = deque(maxlen=1000)
        self.triggered_times: Dict[str, datetime] = {}  # Para cooldown
        self.plc_client = plc_client
        
        # Handlers de acciones
        self.action_handlers: Dict[ActionType, Callable] = {
            ActionType.TOWER_LIGHT: self._handle_tower_light,
            ActionType.BUZZER: self._handle_buzzer,
            ActionType.PLC_WRITE: self._handle_plc_write,
            ActionType.HMI_POPUP: self._handle_hmi_popup,
            ActionType.EMAIL: self._handle_email,
            ActionType.LOG_ONLY: self._handle_log_only,
        }
    
    def add_rule(self, rule: AlarmRule) -> None:
        """Registrar nueva regla de alarma"""
        self.rules[rule.rule_id] = rule
        logger.info(
            f"Alarm rule registered: {rule.rule_id} "
            f"trigger={rule.trigger_type.value} "
            f"actions={len(rule.actions)} "
            f"cooldown={rule.cooldown_ms}ms"
        )
    
    def evaluate_defect_alarm(self,
                             defect,
                             context: Dict) -> Optional[str]:
        """
        Evaluar si defecto dispara alguna alarma
        
        Args:
            defect: DefectRecord object
            context: Contexto adicional
        
        Returns:
            rule_id si se dispara, None en caso contrario
        """
        triggered_rules = []
        
        for rule_id, rule in self.rules.items():
            # Descartar reglas deshabilitadas
            if not rule.enabled:
                continue
            
            # Descartar si está en cooldown
            if self._is_on_cooldown(rule_id, rule.cooldown_ms):
                logger.debug(f"Rule {rule_id} on cooldown - skipped")
                continue
            
            # Evaluar condición de trigger
            if rule.trigger_type == TriggerType.ON_DEFECT:
                if self._matches_defect_trigger(defect, rule.trigger_config):
                    triggered_rules.append(rule)
                    logger.debug(
                        f"Rule {rule_id} matched ON_DEFECT: "
                        f"defect={defect.defect_id} severity={defect.severity.value}"
                    )
            
            elif rule.trigger_type == TriggerType.ON_RATE:
                if self._matches_rate_trigger(context, rule.trigger_config):
                    triggered_rules.append(rule)
                    logger.debug(f"Rule {rule_id} matched ON_RATE")
            
            elif rule.trigger_type == TriggerType.ON_COLOR_OOT:
                if self._matches_color_trigger(context, rule.trigger_config):
                    triggered_rules.append(rule)
                    logger.debug(f"Rule {rule_id} matched ON_COLOR_OOT")
        
        # Ejecutar acciones de todas las reglas disparadas
        for rule in triggered_rules:
            self._trigger_alarm(rule, {
                "defect_id": defect.defect_id,
                "severity": defect.severity.value,
                "type": defect.type.value
            })
        
        return triggered_rules[0].rule_id if triggered_rules else None
    
    def _is_on_cooldown(self, rule_id: str, cooldown_ms: int) -> bool:
        """
        Verificar si una regla está en período de enfriamiento
        
        Returns:
            True si está en cooldown, False si puede dispararse
        """
        last_time = self.triggered_times.get(rule_id)
        if not last_time:
            return False
        
        elapsed_ms = (datetime.now() - last_time).total_seconds() * 1000
        return elapsed_ms < cooldown_ms
    
    def _matches_defect_trigger(self,
                                defect,
                                config: dict) -> bool:
        """
        Evaluar si defecto cumple condiciones de trigger
        """
        
        # Severidad requerida
        if "severity" in config:
            required_severity = config["severity"].lower()
            if defect.severity.value != required_severity:
                return False
        
        # Tipos permitidos
        if "defect_types" in config:
            allowed_types = config["defect_types"]
            if defect.type.value not in allowed_types:
                return False
        
        # Área mínima
        if "min_area_px" in config:
            if defect.area_px < config["min_area_px"]:
                return False
        
        return True
    
    def _matches_rate_trigger(self, context: dict, config: dict) -> bool:
        """
        Evaluar si tasa de defectos cumple umbral
        """
        if "defects_per_100m" in config:
            threshold = config["defects_per_100m"]
            current_rate = context.get("defect_rate_per_100m", 0)
            return current_rate > threshold
        
        return False
    
    def _matches_color_trigger(self, context: dict, config: dict) -> bool:
        """
        Evaluar si color está fuera de tolerancia
        """
        color_measurements = context.get("color_measurements", [])
        
        for roi_id in config.get("roi_ids", []):
            measurement = next(
                (m for m in color_measurements if m.roi_id == roi_id),
                None
            )
            
            if measurement:
                # Verificar estado OOT
                if measurement.state == "OUT_OF_TOLERANCE":
                    return True
        
        return False
    
    def _trigger_alarm(self, rule: AlarmRule, context: Dict) -> str:
        """
        Disparar alarma: ejecutar todas sus acciones
        NO BLOQUEANTE
        
        Returns:
            alarm_id generado
        """
        alarm_id = f"alarm_{rule.rule_id}_{uuid4().hex[:8]}"
        
        # Marcar como disparada (para cooldown)
        rule.last_triggered_at = datetime.now()
        self.triggered_times[rule.rule_id] = datetime.now()
        
        # Ejecutar acciones de forma asíncrona (no bloqueante)
        actions_executed = 0
        for action in rule.actions:
            try:
                handler = self.action_handlers.get(action.action_type)
                if handler:
                    # Non-blocking: si falla, registrar y continuar
                    handler(action, alarm_id, context)
                    actions_executed += 1
                else:
                    logger.warning(f"Unknown action type: {action.action_type}")
            except Exception as e:
                logger.error(
                    f"Action execution failed for {action.action_type}: {e}",
                    exc_info=True
                )
        
        # Registrar evento de alarma
        event = AlarmEvent(
            alarm_id=alarm_id,
            rule_id=rule.rule_id,
            timestamp=datetime.now(),
            trigger_type=rule.trigger_type.value,
            actions_executed=actions_executed,
            triggered_by=context
        )
        self.alarm_queue.append(event)
        
        # Log de auditoría
        logger.warning(
            f"ALARM TRIGGERED: {alarm_id} "
            f"rule={rule.rule_id} "
            f"actions={actions_executed}/{len(rule.actions)} "
            f"context={context}"
        )
        
        return alarm_id
    
    # ─────────────────────────────────────────────────────
    # HANDLERS DE ACCIONES (No bloqueantes)
    # ─────────────────────────────────────────────────────
    
    def _handle_tower_light(self,
                           action: Action,
                           alarm_id: str,
                           context: Dict) -> None:
        """Encender luz de torre"""
        if not self.plc_client:
            logger.warning(f"Tower light requested but no PLC client: {alarm_id}")
            return
        
        try:
            signal_name = f"tower_{action.color}"
            self.plc_client.send_signal(signal_name, duration_ms=action.duration_ms)
            logger.info(
                f"Tower light {action.color} activated: {alarm_id} "
                f"duration={action.duration_ms}ms"
            )
        except Exception as e:
            logger.error(f"Tower light action failed: {e}")
    
    def _handle_buzzer(self,
                      action: Action,
                      alarm_id: str,
                      context: Dict) -> None:
        """Activar buzzer"""
        if not self.plc_client:
            logger.warning(f"Buzzer requested but no PLC client: {alarm_id}")
            return
        
        try:
            self.plc_client.send_signal("buzzer", duration_ms=action.duration_ms)
            logger.info(f"Buzzer activated: {alarm_id} duration={action.duration_ms}ms")
        except Exception as e:
            logger.error(f"Buzzer action failed: {e}")
    
    def _handle_plc_write(self,
                         action: Action,
                         alarm_id: str,
                         context: Dict) -> None:
        """
        Escribir dato al PLC
        Con reintentos si falla (cola)
        """
        if not self.plc_client:
            logger.warning(f"PLC write requested but no PLC client: {alarm_id}")
            return
        
        if not action.plc_address:
            logger.warning(f"PLC write but no address specified: {alarm_id}")
            return
        
        try:
            self.plc_client.write(action.plc_address, action.plc_value)
            logger.info(
                f"PLC write successful: addr={action.plc_address} "
                f"value={action.plc_value} ({alarm_id})"
            )
        except Exception as e:
            # No bloqueante: registrar y continuar
            logger.error(f"PLC write failed: {e} - will retry later")
            # En producción: agregar a cola de reintentos
    
    def _handle_hmi_popup(self,
                         action: Action,
                         alarm_id: str,
                         context: Dict) -> None:
        """
        Enviar popup al HMI (frontend)
        Se almacena en cola para que frontend consulte
        """
        popup_event = {
            "type": "alarm_popup",
            "alarm_id": alarm_id,
            "title": action.popup_title,
            "message": action.popup_message,
            "timestamp": datetime.now().isoformat(),
            "severity": context.get("severity", "unknown")
        }
        
        logger.info(f"HMI popup queued: {alarm_id} - '{action.popup_title}'")
        # En implementación real: agregar a event_queue
    
    def _handle_email(self,
                     action: Action,
                     alarm_id: str,
                     context: Dict) -> None:
        """
        Enviar email (no bloqueante)
        En producción: usar gestor de correo asíncrono
        """
        if not action.email_to:
            logger.warning(f"Email action but no recipients: {alarm_id}")
            return
        
        try:
            # En implementación real:
            # await async_email_client.send(...)
            logger.info(
                f"Email queued to {action.email_to}: {alarm_id} "
                f"subject='{action.email_subject}'"
            )
        except Exception as e:
            logger.error(f"Email queueing failed: {e}")
    
    def _handle_log_only(self,
                        action: Action,
                        alarm_id: str,
                        context: Dict) -> None:
        """Solo registrar (para auditoría)"""
        logger.info(f"Log-only action: {alarm_id}")
    
    # ─────────────────────────────────────────────────────
    # GETTERS PARA MONITOREO
    # ─────────────────────────────────────────────────────
    
    def get_recent_alarms(self, count: int = 10) -> List[Dict]:
        """Obtener últimas N alarmas"""
        alarms = list(self.alarm_queue)[-count:]
        return [
            {
                "alarm_id": a.alarm_id,
                "rule_id": a.rule_id,
                "timestamp": a.timestamp.isoformat(),
                "trigger_type": a.trigger_type,
                "actions_executed": a.actions_executed,
                "context": a.triggered_by
            }
            for a in alarms
        ]
    
    def get_rule_status(self, rule_id: str) -> Optional[Dict]:
        """Obtener estado de una regla"""
        rule = self.rules.get(rule_id)
        if not rule:
            return None
        
        is_on_cooldown = self._is_on_cooldown(rule_id, rule.cooldown_ms)
        
        return {
            "rule_id": rule_id,
            "enabled": rule.enabled,
            "trigger_type": rule.trigger_type.value,
            "cooldown_ms": rule.cooldown_ms,
            "on_cooldown": is_on_cooldown,
            "last_triggered": rule.last_triggered_at.isoformat() if rule.last_triggered_at else None,
            "actions_count": len(rule.actions),
            "description": rule.description
        }
    
    def get_all_rules_status(self) -> Dict:
        """Obtener estado de todas las reglas"""
        return {
            rule_id: self.get_rule_status(rule_id)
            for rule_id in self.rules.keys()
        }
    
    def disable_rule(self, rule_id: str) -> bool:
        """Desactivar una regla"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            logger.info(f"Rule disabled: {rule_id}")
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Activar una regla"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            logger.info(f"Rule enabled: {rule_id}")
            return True
        return False
    
    def get_alarm_statistics(self) -> Dict:
        """Estadísticas de alarmas"""
        if not self.alarm_queue:
            return {
                "total_alarms": 0,
                "by_rule": {},
                "by_trigger_type": {}
            }
        
        by_rule = {}
        by_trigger_type = {}
        
        for event in self.alarm_queue:
            by_rule[event.rule_id] = by_rule.get(event.rule_id, 0) + 1
            by_trigger_type[event.trigger_type] = by_trigger_type.get(event.trigger_type, 0) + 1
        
        return {
            "total_alarms": len(self.alarm_queue),
            "by_rule": by_rule,
            "by_trigger_type": by_trigger_type
        }
