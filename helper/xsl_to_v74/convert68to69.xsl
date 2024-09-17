<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:output method="xml"
        indent="yes" omit-xml-declaration="no" encoding="utf-8"/>

<!-- default rule -->
<xsl:template match="*" mode="conv68to69">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv68to69"/>
    </xsl:copy>  
</xsl:template>

<!-- version update -->
<para xmlns="http://docbook.org/ns/docbook">
    Changed attribute <tag class="attribute">schemaversion</tag>
    to <tag class="attribute">schemaversion</tag> from
    <literal>6.8</literal> to <literal>6.9</literal>.
</para>
<xsl:template match="image" mode="conv68to69">
    <xsl:choose>
        <!-- nothing to do if already at 6.9 -->
        <xsl:when test="@schemaversion > 6.8">
            <xsl:copy-of select="."/>
        </xsl:when>
        <!-- otherwise apply templates -->
        <xsl:otherwise>
            <image schemaversion="6.9">
                <xsl:copy-of select="@*[local-name() != 'schemaversion']"/>
                <xsl:apply-templates  mode="conv68to69"/>  
            </image>
        </xsl:otherwise>
    </xsl:choose>
</xsl:template>

<!-- toplevel processing instructions and comments -->
<xsl:template match="processing-instruction()|comment()" mode="conv68to69">
    <xsl:copy>
        <xsl:copy-of select="@*"/>
        <xsl:apply-templates mode="conv68to69"/>
    </xsl:copy>
</xsl:template>

<!-- delete hybrid attribute from type -->
<para xmlns="http://docbook.org/ns/docbook">
    Delete hybrid attribute from type
</para>
<xsl:template match="type" mode="conv68to69">
    <type>
        <xsl:copy-of select="@*[not(local-name(.) = 'hybrid')]"/>
        <xsl:apply-templates mode="conv68to69"/>
    </type>
</xsl:template>

<!-- delete oem-ataraid-scan element from oemconfig -->
<xsl:template match="oemconfig/oem-ataraid-scan" mode="conv68to69">
</xsl:template>

</xsl:stylesheet>
