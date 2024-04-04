<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv58to59">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv58to59"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>5.8</literal> to <literal>5.9</literal>.
</para>
<xsl:template match="image" mode="conv58to59">
    <xsl:choose>
        <!-- nothing to do if already at 5.9 -->
        <xsl:when test="@schemaversion > 5.8">
            <xsl:copy-of select="/"/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="5.9">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv58to59"/>
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- rename controller="scsi" to controller="lsilogic" in vmdisk -->
<para xmlns="http://docbook.org/ns/docbook">
    rename controller="scsi" to controller="lsilogic" in vmdisk
</para>
<xsl:template match="vmdisk" mode="conv58to59">
    <vmdisk>
        <xsl:copy-of select="@*[not(local-name(.) = 'controller')]"/>
        <xsl:choose>
            <xsl:when test="@controller='scsi'">
                <xsl:variable name="controllername" select='"lsilogic"'/>
                <xsl:attribute name="controller">
                    <xsl:value-of select="$controllername"/>
                </xsl:attribute>
            </xsl:when>
            <xsl:when test="@controller!='scsi'">
                <xsl:variable name="controllername" select="@controller"/>
                <xsl:attribute name="controller">
                    <xsl:value-of select="$controllername"/>
                </xsl:attribute>
            </xsl:when>
                </xsl:choose>
        <xsl:apply-templates mode="conv58to59"/>
    </vmdisk>
</xsl:template>

</xsl:stylesheet>
