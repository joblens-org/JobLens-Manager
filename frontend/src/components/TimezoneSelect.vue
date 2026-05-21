<template>
  <el-select
    v-model="model"
    filterable
    allow-create
    :placeholder="placeholder"
    :size="size"
    :disabled="disabled"
  >
    <el-option
      v-for="tz in commonTimezones"
      :key="tz"
      :label="tz"
      :value="tz"
    />
  </el-select>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = withDefaults(
  defineProps<{
    modelValue: string
    placeholder?: string
    size?: 'small' | 'default' | 'large'
    disabled?: boolean
  }>(),
  {
    placeholder: () => t('timezone.placeholder'),
    size: 'default',
    disabled: false,
  },
)

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const model = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const commonTimezones = [
  'Asia/Shanghai',
  'Asia/Tokyo',
  'Asia/Seoul',
  'Asia/Singapore',
  'Asia/Kolkata',
  'Asia/Dubai',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Europe/Moscow',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Sao_Paulo',
  'Pacific/Auckland',
  'Australia/Sydney',
  'UTC',
]
</script>
