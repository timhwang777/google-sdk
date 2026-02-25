# Data Model: Google API Python SDK

**Phase 1 Output** | **Date**: 2026-02-23

## Base Models

### BaseResource
- **Fields**: `id: str`, `kind: str | None`
- **Config**: `extra="allow"`, `populate_by_name=True`
- **Purpose**: All Google API resource models inherit from this

### PageResponse[T]
- **Fields**: `items: list[T]`, `next_page_token: str | None = Field(alias="nextPageToken")`
- **Purpose**: Generic wrapper for paginated API responses

---

## Auth Models

### TokenData
- **Fields**: `token: str`, `refresh_token: str | None`, `token_uri: str | None`, `client_id: str | None`, `client_secret: str | None`, `scopes: list[str]`, `expiry: datetime | None`
- **Purpose**: Serializable token representation for TokenStore backends

---

## Google Drive Models

### File
- **Fields**: `id: str`, `name: str`, `mime_type: str = Field(alias="mimeType")`, `size: int | None = None`, `created_time: datetime | None = Field(None, alias="createdTime")`, `modified_time: datetime | None = Field(None, alias="modifiedTime")`, `parents: list[str] | None = None`, `web_view_link: str | None = Field(None, alias="webViewLink")`, `trashed: bool = False`
- **Relationships**: belongs to Folder (via parents), has many Permission
- **Convenience methods**: `download()`, `delete()`, `move()`, `copy()`, `share()`

### Folder (extends File)
- **Fields**: inherits File, `mime_type` defaults to `"application/vnd.google-apps.folder"`
- **Convenience methods**: `list_children()`, `create_subfolder()`

### Permission
- **Fields**: `id: str`, `type: str` (user|group|domain|anyone), `role: str` (owner|organizer|writer|commenter|reader), `email_address: str | None = Field(None, alias="emailAddress")`, `domain: str | None = None`, `display_name: str | None = Field(None, alias="displayName")`
- **Relationships**: belongs to File

### UploadProgress
- **Fields**: `bytes_sent: int`, `total_bytes: int`, `percentage: float`
- **Purpose**: Progress callback payload for resumable uploads

---

## Google Calendar Models

### Calendar
- **Fields**: `id: str`, `summary: str`, `description: str | None = None`, `time_zone: str | None = Field(None, alias="timeZone")`, `location: str | None = None`, `primary: bool = False`
- **Relationships**: has many Event
- **Convenience methods**: `list_events()`, `create_event()`

### Event
- **Fields**: `id: str`, `summary: str | None = None`, `description: str | None = None`, `location: str | None = None`, `start: EventDateTime`, `end: EventDateTime`, `status: str = "confirmed"` (confirmed|tentative|cancelled), `attendees: list[Attendee] = []`, `recurrence: list[str] | None = None`, `recurring_event_id: str | None = Field(None, alias="recurringEventId")`, `html_link: str | None = Field(None, alias="htmlLink")`, `hangout_link: str | None = Field(None, alias="hangoutLink")`, `conference_data: ConferenceData | None = Field(None, alias="conferenceData")`, `organizer: EventPerson | None = None`, `creator: EventPerson | None = None`, `reminders: EventReminders | None = None`, `created: datetime | None = None`, `updated: datetime | None = None`
- **Relationships**: belongs to Calendar, has many Attendee
- **Convenience methods**: `accept()`, `decline()`, `update()`, `delete()`

### EventDateTime
- **Fields**: `date_time: datetime | None = Field(None, alias="dateTime")`, `date: str | None = None`, `time_zone: str | None = Field(None, alias="timeZone")`
- **Purpose**: Handles both timed and all-day events

### Attendee
- **Fields**: `email: str`, `display_name: str | None = Field(None, alias="displayName")`, `response_status: str = Field("needsAction", alias="responseStatus")` (needsAction|declined|tentative|accepted), `organizer: bool = False`, `self_: bool = Field(False, alias="self")`, `optional: bool = False`

### EventPerson
- **Fields**: `email: str | None = None`, `display_name: str | None = Field(None, alias="displayName")`, `self_: bool = Field(False, alias="self")`

### EventReminders
- **Fields**: `use_default: bool = Field(True, alias="useDefault")`, `overrides: list[ReminderOverride] = []`

### ReminderOverride
- **Fields**: `method: str` (email|popup), `minutes: int`

### ConferenceData
- **Fields**: `conference_id: str | None = Field(None, alias="conferenceId")`, `entry_points: list[EntryPoint] = Field([], alias="entryPoints")`, `conference_solution: ConferenceSolution | None = Field(None, alias="conferenceSolution")`

### EntryPoint
- **Fields**: `entry_point_type: str = Field(alias="entryPointType")`, `uri: str`, `label: str | None = None`

### ConferenceSolution
- **Fields**: `name: str`, `icon_uri: str | None = Field(None, alias="iconUri")`

### FreeBusyRequest
- **Fields**: `time_min: datetime = Field(alias="timeMin")`, `time_max: datetime = Field(alias="timeMax")`, `items: list[dict]`, `time_zone: str | None = Field(None, alias="timeZone")`

### FreeBusyResponse
- **Fields**: `calendars: dict[str, FreeBusyCalendar]`

### FreeBusyCalendar
- **Fields**: `busy: list[TimePeriod]`, `errors: list[dict] = []`

### TimePeriod
- **Fields**: `start: datetime`, `end: datetime`

---

## Google Meet Models

### Space
- **Fields**: `name: str`, `meeting_uri: str | None = Field(None, alias="meetingUri")`, `meeting_code: str | None = Field(None, alias="meetingCode")`, `config: SpaceConfig | None = None`
- **Convenience methods**: `get_participants()`, `end()`

### SpaceConfig
- **Fields**: `access_type: str = Field("OPEN", alias="accessType")` (OPEN|TRUSTED|RESTRICTED), `entry_point_access: str = Field("ALL", alias="entryPointAccess")`

### Participant
- **Fields**: `name: str | None = None`, `earliest_start_time: datetime | None = Field(None, alias="earliestStartTime")`, `latest_end_time: datetime | None = Field(None, alias="latestEndTime")`, `signin_user: SignInUser | None = Field(None, alias="signedinUser")`, `anonymous_user: AnonymousUser | None = Field(None, alias="anonymousUser")`, `phone_user: PhoneUser | None = Field(None, alias="phoneUser")`

### SignInUser
- **Fields**: `user: str | None = None`, `display_name: str | None = Field(None, alias="displayName")`

### AnonymousUser
- **Fields**: `display_name: str | None = Field(None, alias="displayName")`

### PhoneUser
- **Fields**: `display_name: str | None = Field(None, alias="displayName")`

### ParticipantSession
- **Fields**: `name: str | None = None`, `start_time: datetime | None = Field(None, alias="startTime")`, `end_time: datetime | None = Field(None, alias="endTime")`

### Recording
- **Fields**: `name: str | None = None`, `state: str | None = None` (STARTED|ENDED), `start_time: datetime | None = Field(None, alias="startTime")`, `end_time: datetime | None = Field(None, alias="endTime")`, `drive_destination: DriveDestination | None = Field(None, alias="driveDestination")`

### DriveDestination
- **Fields**: `file: str | None = None`, `export_uri: str | None = Field(None, alias="exportUri")`

---

## Transport / Config Models

### SDKConfig
- **Fields**: `timeout: float = 30.0`, `max_retries: int = 3`, `max_backoff: float = 60.0`, `rate_limit_per_second: float | None = None`, `log_level: str = "WARNING"`, `log_format: str = "text"` (text|json)

### RetryConfig
- **Fields**: `max_retries: int = 3`, `max_backoff: float = 60.0`, `retryable_status_codes: set[int] = {429, 500, 502, 503, 504}`

---

## State Transitions

### Event.status
```
confirmed -> tentative -> cancelled
confirmed -> cancelled
```

### Recording.state
```
STARTED -> ENDED
```

### Upload (internal)
```
PENDING -> INITIATING -> UPLOADING -> COMPLETED
UPLOADING -> FAILED -> UPLOADING (resume)
```
